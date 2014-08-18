from func import *
from classes import *


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

		elif block_is_ulist(block):
			items = []
			for line in block:
				items.append(ListItem(ulist_item_text(line)))
			nodes.append(UList(items))

		elif block_is_olist(block):
			items = []
			for line in block:
				items.append(ListItem(olist_item_text(line)))
			nodes.append(OList(items))

		elif block_is_code(block):
			nodes.append(CodeBlock(map(Plaintext, block[1:-1])))

		elif block_is_math(block):
			nodes.append(MathBlock(map(parse_math, block[1:-1])))

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
						break
					else:
						raise Exception("Expected closing tag for %s, found %s", (tos_token, token))
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
			node_stack[-1].children.append(parse_math(text))

	return node_stack[0]


def parse_math(text):
	stack = ['Math_OPEN']
	node_stack = [Math()]

	for token, text in get_math_tokens(text):
		node_class = globals()[token]

		if token == 'FANCY TOKENS':
			pass
		else:  # text tokens
			node_stack[-1].children.append(node_class(text))

	return node_stack[0]


if __name__ == "__main__":
	with open("text.txt", 'r') as f:
		doc = parse(f)
		print(doc.emit_html())