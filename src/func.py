from re import sub, compile, match, UNICODE

# Init RE objects
re_flags = UNICODE
re_ulistitem = compile(r'^\*\s?', flags=re_flags)
re_olistitem = compile(r'^\d+\.\s?', flags=re_flags)


def get_blocks(file):
	block = []
	for line in file:
		if line.strip():
			block.append(line)
		else:
			if block:
				yield block
				block = []

	if block:
		yield block


def block_is_heading(block):
	last_line = block[-1]
	for char in last_line:
		if char not in "=\n":
			return False
	return True


def block_is_subheading(block):
	last_line = block[-1]
	for char in last_line:
		if char not in "-\n":
			return False
	return True


def block_is_ulist(block):
	for line in block:
		if not match(re_ulistitem, line):
			return False
	return True


def block_is_olist(block):
	for line in block:
		if not match(re_olistitem, line):
			return False
	return True


def ulist_item_text(item):
	return sub(re_ulistitem, '', item)


def olist_item_text(item):
	return sub(re_olistitem, '', item)