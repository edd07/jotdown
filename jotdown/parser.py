# -*- coding: utf-8 -*-
from typing import Iterator, Iterable, Union, TextIO, List

from jotdown.lexer import *
from jotdown.classes import *
from jotdown.errors import LineNumberException, ContextException, MissingTagException
import jotdown.globalv as globalv

import sys


def parse(file: Union[Iterable, TextIO]) -> Document:
	"""
	Returns a Document Node, the root of a syntax tree. Splits a file into Blocks and parses their contents individually
	"""

	blocks = get_blocks(file)
	nodes = []
	for line_offset, block in blocks:
		if block_is_horizontal_rule(block):
			nodes.append(HorizontalRule())

		elif block_is_heading(block):
			level, text = lex_heading(block)
			subnodes = []
			for line in text:
				subnodes.append(Node(parse_text(line_offset, line)))
			nodes.append(Heading(level, subnodes))

		elif block_is_list(block):
			nodes.append(_parse_list(line_offset, block))

		elif block_is_code(block):
			nodes.append(CodeBlock(map(Plaintext, block[1:-1])))

		elif block_is_math(block):
			nodes.append(MathBlock([parse_math(line_offset + 1, replace_math(''.join(block[1:-1])))]))

		elif block_is_md_table(block):
			nodes.append(_parse_table(line_offset, block))

		elif block_is_blockquote(block):
			nodes.append(_parse_blockquote(line_offset, block))
		else:
			# Default case, paragraphs
			subnodes = []
			for line in block:
				text_nodes = parse_text(line_offset, line)
				if text_nodes:
					subnodes.append(Node(text_nodes))
			if subnodes:
				nodes.append(Paragraph(subnodes))

	return Document(nodes)


def parse_text(line_number: int, text: str) -> Sequence[Node]:
	"""
	Returns a Node, root to a syntax subtree, from plain text
	"""

	# Start the parser up with a dummy top-level node
	# Keep track of the nested nodes and their type
	stack: List[Tuple[str, Node]] = [('Dummy_OPEN', Node())]

	for token, groups in get_text_tokens(line_number, text):
		if token.endswith('_OPEN'):
			# General rule for NODE_OPEN or NODE_CLOSE tokens
			node_type, *node_subtypes, open_or_close = token.split('_')
			node_class = globals()[node_type]
			stack.append((token, node_class()))

		elif token.endswith('_CLOSE'):
			node_type, *node_subtypes, open_or_close = token.split('_')
			tos_token, _ = stack[-1]
			tos_node_type, *tos_subtypes, tos_open_or_close = tos_token.split('_')
			if not tos_node_type == 'Dummy':
				if (
						tos_node_type == node_type and tos_subtypes == node_subtypes
						and tos_open_or_close == 'OPEN'
				):
					_, closed_node = stack.pop()
					stack[-1][1].children.append(closed_node)
				else:
					# TODO: point out the characters where the tag is opened
					# TODO: this is never called. When opening a new node, check that one of the same
					# type is not awaiting closure on the stack
					raise MissingTagException(line_number, tos_token, encountered_tag=token)
			else:
				# Trying to close a tag that was never opened
				raise MissingTagException(line_number, token, opening=True)

		elif token.endswith('_AMB'):
			# General rules for tags opened and closed by the same token
			if token == stack[-1][0]:
				# Close the node
				_, closed_node = stack.pop()
				stack[-1][1].children.append(closed_node)
			else:
				# Open a node
				node_type, *_, _ = token.split('_')
				node_class = globals()[node_type]
				stack.append((token, node_class()))

		elif token == "Plaintext":
			# Combine consecutive Plaintext nodes to reduce the overall number of Nodes created
			tos_children = stack[-1][1].children
			if tos_children and isinstance(tos_children[-1], Plaintext):
				tos_children[-1].text += groups[0]
			else:
				stack[-1][1].children.append(Plaintext(groups[0]))

		elif token == "Math":
			stack[-1][1].children.append(parse_math(line_number, replace_math(groups[0])))

		elif token == "ImplicitLink":
			stack[-1][1].children.append(ImplicitLink(TextNode(groups[0]), groups[0]))

		elif token == "ImplicitEmail":
			stack[-1][1].children.append(ImplicitLink(TextNode(groups[0]), f'mailto: {groups[0]}'))

		elif token == "Link":
			text, href = groups
			stack[-1][1].children.append(Link(Node(parse_text(line_number, text)), href))

		elif token == "ReferenceLink":
			cited_text, ref_key = groups
			stack[-1][1].children.append(ReferenceLink(Node(parse_text(line_number, cited_text)), ref_key))
			globalv.references[ref_key] = None  # Save its place in the OrderedDict

		elif token == "ReferenceDef":
			ref_key, reference_text = groups

			# TODO: Should parse on emit, or only when reference mode is enabled
			globalv.references[ref_key] = Node(parse_text(line_number, reference_text)), reference_text

		elif token == "Image":
			alt, src, title = groups
			alt = Node(parse_text(line_number, alt)) if alt else TextNode('')
			title = Node(parse_text(line_number, title)) if title else TextNode('')
			stack[-1][1].children.append(Content(alt, src, title))

	if len(stack) > 1:
		raise MissingTagException(line_number, stack[-1][0])
	return stack[0][1].children


def parse_math(line_offset: int, text: str) -> Math:
	"""
	Returns a Math Node from a plain text
	"""

	# Keep track of the nested nodes and their types
	stack = ['Math_OPEN']
	node_stack = [Math()]
	debug_text = text[:50] if len(text) <= 50 else text[:47] + '...'  # For error messages
	line_number = line_offset

	for line_number, token, text in get_math_tokens(line_offset, text):
		if '_OPEN' in token:
			node_class = globals()[token.split('_')[0]]
			stack.append(token)
			node_stack.append(node_class())
		elif '_CLOSE' in token:
			node, _ = token.split('_')
			tos_token = stack[-1]
			if '_' in tos_token:
				tos_node, tos_type = tos_token.split('_')
				if tos_node == node and tos_type == 'OPEN' \
					or tos_node in bracket_closable and tos_type == 'OPEN' and node == 'Brackets':
					stack.pop()
					closed_node = node_stack.pop()
					node_stack[-1].children.append(closed_node)
				else:
					raise Exception("Expected closing math tag for %s at line %d, found %s" % (tos_token, line_number, token))
			else:
				raise Exception("Malformed document at line %d: %s" % (line_number, text))
		else:  # text tokens
			node_class = globals()[token]  # TODO: Read from the module, not the globals
			node_stack[-1].children.append(node_class(text))

	if len(stack) > 1:
		raise Exception("Missing closing math tag for %s at line %d: %s" % (stack[-1], line_number, repr(debug_text)))
	return node_stack[0]


def _parse_list(line_offset: int, block: Block) -> ListNode:
	"""
	Returns a ListNode (ordered, unordered or checklist) from a block of text
	"""
	# Keep track of nested lists and their indent levels
	list_stack = []
	indent_stack = [-1]

	for line_number, line in enumerate(block, line_offset):
		# Figure out the type of list
		list_type = 'checklist'  # by default
		m = re_checklistitem.match(line)
		if not m:
			list_type = 'unordered'
			m = re_ulistitem.match(line)
			if not m:
				list_type = 'ordered'
				m = re_olistitem.match(line)
				if not m:
					raise Exception('Malformed list item at line %d: %s' % (line_number, line))

		# Indent level of the current line
		new_indent = len(m.group(1))

		if new_indent > indent_stack[-1]:
			# Need to create new nested lists
			while new_indent > indent_stack[-1]:
				indent_stack.append(indent_stack[-1] + 1)

				if list_type == 'ordered':
					olist_type, start = lex_olist(m)
					list_stack.append(OList(list_type=olist_type, start=start))
				elif list_type == 'unordered':
					list_stack.append(UList())
				elif list_type == 'checklist':
					list_stack.append(CheckList())
		# Need to close nested lists?
		while new_indent < indent_stack[-1]:
			indent_stack.pop()
			closed_list = list_stack.pop()
			list_stack[-1].children[-1].children.append(closed_list)

		# If checklist, set its state
		if isinstance(list_stack[-1], CheckList):
			m = re_checklistitem.match(line)
			checked = bool(m.group(2))
			list_stack[-1].children.append(ChecklistItem(checked, parse_text(line_number, list_item_text(line))))
		else:
			list_stack[-1].children.append(ListItem(parse_text(line_number, list_item_text(line))))

	# Finish closing remaining nested lists
	while len(list_stack) > 1:
		closed_list = list_stack.pop()
		list_stack[-1].children.append(closed_list)

	return list_stack[0]


def _parse_table(line_offset: int, block: Block) -> Table:
	"""
	Returns a Table Node from a block of text
	"""

	header_content = block[0].split('|')
	header = [TableHeader(parse_text(line_offset, i)) for i in header_content]

	column_alignment = list(map(_cell_align, block[1].split('|')))

	# Check if there is a caption
	md_table = block[2:]
	caption = None
	if len(block) > 5:
		for char in block[-2]:
			if char not in '\t\n -':
				break
		else:
			caption = parse_text(line_offset + len(block) - 1, block[-1])
			md_table = block[2:-2]

	table = Table(caption, column_alignment, [TableRow(header)])

	for line_number, line in enumerate(md_table, line_offset + 2):
		cells = []
		for content, cell_alignment in zip(line.split('|'), column_alignment):
			cells.append(TableCell(cell_alignment, parse_text(line_number, content)))
		table.children.append(TableRow(cells))

	return table


def _parse_blockquote(line_offset: int, block: Block) -> Blockquote:
	blockquote_stack = []
	indent_stack = [0]

	for line_number, line in enumerate(block, line_offset):
		m = re_blockquoteline.match(line)
		if m.group(1):
			new_indent = m.group(1).count('>')
		else:
			new_indent = 1

		if new_indent > indent_stack[-1]:  # Create new nested Blockquotes
			while new_indent > indent_stack[-1]:
				indent_stack.append(indent_stack[-1] + 1)
				blockquote_stack.append(Blockquote())

		while new_indent < indent_stack[-1]:  # Close blockquotes on de-indent
			indent_stack.pop()
			closed_block = blockquote_stack.pop()
			blockquote_stack[-1].children.append(closed_block)

		blockquote_stack[-1].children.append(Node(parse_text(line_number, re_blockquoteline.sub('', line))))

	while len(blockquote_stack) > 1:
		indent_stack.pop()
		closed_block = blockquote_stack.pop()
		blockquote_stack[-1].children.append(closed_block)

	return blockquote_stack[-1]


def _remove_gt(line: str) -> str:
	"""
	Remove the leading greater-than signs from lines belonging to a blockquote
	"""
	if line[0] == '>':
		return line[1:]
	else:
		return line


def _cell_align(cell: str) -> int:
	if cell.endswith('-'):
		return 0  # Left
	elif cell.startswith('-'):
		return 2  # Right
	else:
		return 1  # Center

