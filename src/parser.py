from func import *
from classes import *


def parse(file):

	blocks = get_blocks(file)
	nodes = []
	for block in blocks:
		if block_is_heading(block):
			text = block[:-1]
			nodes.append(Heading(text))

		elif block_is_subheading(block):
			text = block[:-1]
			nodes.append(Subheading(text))

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
			nodes.append(CodeBlock(block[1:-1]))

		else:
			nodes.append(Paragraph(block))

	return Document(nodes)


def parse_text(text):
	stack = []

	for token, text in get_tokens(text):
		if '_' in token:
			# General rule for NODE_OPEN or NODE_CLOSE tokens
			node, type = token.split('_')

			if type == 'OPEN':
				stack.append(token)
			else:
				#TODO: Search and pop the stack until close"
				pass


if __name__ == "__main__":
	with open("text.txt", 'r') as f:
		doc = parse(f)
		print(doc.emit_html())