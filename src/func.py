from re import sub, compile, match, UNICODE

# Init RE objects
re_flags = UNICODE
re_ulistitem = compile(r'^\*\s*', flags=re_flags)
re_olistitem = compile(r'^\d+\.\s*', flags=re_flags)
re_code_delim = compile(r'^```\s*$', flags=re_flags)

# Token definitions for text parsing

tokens = [
	(r'\b`', 'CODE_OPEN'),
    (r'[^\\]`\b', 'CODE_CLOSE'),

    (r'\b**', 'STRONG_OPEN'),
    (r'**\b', 'STRONG_CLOSE'),
    (r'\b__', 'STRONG_OPEN'),
    (r'__\b', 'STRONG_CLOSE'),

    (r'\b*', 'EMPH_OPEN'),
    (r'*\b', 'EMPH_CLOSE'),
    (r'\b_', 'EMPH_OPEN'),
    (r'_\b', 'EMPH_CLOSE'),

	(r'\B*\b', 'NORMAL')

]

tokens = [(compile(exp, flags=re_flags), val) for (exp, val) in tokens]


def get_blocks(file):
	block = []
	in_code_block = False
	for line in file:

		if match(re_code_delim, line):
			in_code_block = not in_code_block

		if not line.strip() and not in_code_block:
			if block:
				yield block
			block = []
		else:
			block.append(line)

	if block:
		yield block


def get_tokens(text):
	while text:
		for exp, val in tokens:
			m = match(exp, text)

			if m:
				m_len = len(m.group[0])

				yield val, m.group[0]

				text = text[m_len:]
				break


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


def block_is_code(block):
	return match(re_code_delim, block[0]) and match(re_code_delim, block[-1])


def ulist_item_text(item):
	return sub(re_ulistitem, '', item)


def olist_item_text(item):
	return sub(re_olistitem, '', item)