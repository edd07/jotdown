# -*- coding: utf-8 -*-

from func import *
from classes import *
import sys


def parse(file):
	# Block-level "parser"
	blocks = get_blocks(file)
	nodes = []
	for block in blocks:
		if block_is_heading(block):
			text = block[:-1]
			nodes.append(Heading(map(parse_text, text)))

		elif block_is_subheading(block):
			text = block[:-1]
			nodes.append(Subheading(map(parse_text, text)))

		elif block_is_list(block):
			list_stack = []
			indent = -1

			for line in block:
				m = match(re_listitem, line)
				new_indent = len(m.group(1))

				if new_indent > indent:
					indent = new_indent
					is_olist = bool(match(re_olistitem, line))
					if is_olist:
						list_stack.append(OList())
					else:
						list_stack.append(UList())
				elif new_indent < indent:
					indent = new_indent
					closed_list = list_stack.pop()
					list_stack[-1].children.append(closed_list)

				list_stack[-1].children.append(ListItem([parse_text(list_item_text(line))]))

			while len(list_stack) > 1:
				closed_list = list_stack.pop()
				list_stack[-1].children.append(closed_list)

			nodes.append(list_stack[0])

		elif block_is_code(block):
			nodes.append(CodeBlock(map(Plaintext, block[1:-1])))

		elif block_is_math(block):
			nodes.append(MathBlock([parse_math(replace_math('\n'.join(block[1:-1])))]))

		elif block_is_md_table(block):
			header_content = map(parse_text, block[0].split('|'))
			header = [TableHeader([i]) for i in header_content]

			alignment = list(map(cell_align, block[1].split('|')))
			table = Table([TableRow(header)])

			for line in block[2:]:
				cells = []
				for content, align in zip(line.split('|'), alignment):
					cells.append(TableCell(align, [parse_text(content)]))
				table.children.append(TableRow(cells))

			nodes.append(table)

		else:
			nodes.append(Paragraph(map(parse_text, block)))

	return Document(nodes)


def parse_text(text):
	# (Formattable text)-level parser

	stack = ['Text_OPEN']
	node_stack = [Text()]

	for token, text in get_text_tokens(text):
		if '_OPEN' in token or '_CLOSE' in token:
			# General rule for NODE_OPEN or NODE_CLOSE tokens
			node, type = token.split('_')

			if type == 'OPEN':
				stack.append(token)
				node_class = globals()[node]
				node_stack.append(node_class())
			else:

				tos_token = stack[-1]
				if '_' in tos_token:
					tos_node, tos_type = tos_token.split('_')
					if tos_node == node and tos_type == 'OPEN':
						stack.pop()
						closed_node = node_stack.pop()
						node_stack[-1].children.append(closed_node)
					else:
						raise Exception("Expected closing tag for %s, found %s" % (tos_token, token))
				else:
					raise Exception("Malformed document at %s" % text)

		elif '_AMB' in token:
			# General rules for tags opened and closed by the same token
			if token == stack[-1]:
				# Close the node
				stack.pop()
				closed_node = node_stack.pop()
				node_stack[-1].children.append(closed_node)
			else:
				# Open a node
				node, _ = token.split('_')
				stack.append(token)
				node_class = globals()[node]
				node_stack.append(node_class())

		elif token == "Plaintext":
			node_stack[-1].children.append(Plaintext(text))

		elif token == "Math":
			node_stack[-1].children.append(parse_math(replace_math(text)))

	return node_stack[0]


def parse_math(text):
	stack = ['Math_OPEN']
	node_stack = [Math()]

	for token, text in get_math_tokens(text):
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
					or tos_node in parens_closable and tos_type == 'OPEN':
					stack.pop()
					closed_node = node_stack.pop()
					node_stack[-1].children.append(closed_node)
				else:
					raise Exception("Expected closing math tag for %s, found %s" % (tos_token, token))
			else:
				raise Exception("Malformed document at %s" % text)
		else:  # text tokens
			node_class = globals()[token]
			node_stack[-1].children.append(node_class(text))

	return node_stack[0]


if __name__ == "__main__":

	if len(sys.argv) > 1:
		fname = sys.argv[1]
	else:
		fname = "text.txt"

	if len(sys.argv) > 2:
		out = sys.argv[2]
	else:
		out = "out.html"

	with open(fname, 'r') as f, open(out, 'wb') as fout:
		doc = parse(f)
		fout.write(doc.emit_html())