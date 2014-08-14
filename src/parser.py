from func import *
from classes import *


def parse(file):

	blocks = get_blocks(file)
	nodes = []
	for block in blocks:
		if block_is_heading(block):
			text = "\n".join(block[:-1])
			nodes.append(Heading(text))

		elif block_is_subheading(block):
			text = "\n".join(block[:-1])
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

		else:
			# Text paragraph
			pass

	return Document(nodes)


if __name__ == "__main__":
	with open("text.txt", 'r') as f:
		doc = parse(f)
		print(doc.emit_html())