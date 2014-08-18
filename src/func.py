from re import sub, compile, match, UNICODE

# Init RE objects
re_flags = UNICODE
re_ulistitem = compile(r'^\*\s*', flags=re_flags)
re_olistitem = compile(r'^\d+\.\s*', flags=re_flags)
re_code_delim = compile(r'^```\s*$', flags=re_flags)
re_math_open = compile(r'^«««\s*$', flags=re_flags)
re_math_close = compile(r'^»»»\s*$', flags=re_flags)

# Token definitions for text parsing

text_tokens = [
	(r'`', 'CodeInline_AMB'),

    (r'\*\*', 'Strong_AMB'),
    (r'\b__', 'Strong_AMB'),

    (r'\*', 'Emph_AMB'),
    (r'\b_', 'Emph_AMB'),

    (r'«', 'MathInline_OPEN'),
    (r'»', 'MathInline_CLOSE'),

	(r'(?:[^_\*`«»]|\\[^_\*`«»])+', 'Plaintext')

]

math_tokens = [
	(r'\B_(\w+)', 'Subscript'),
    (r'\B\^(\w+)', 'Superscript'),
	(r'\b([^\W_]+)', 'Identifier'),
	(r'([\+\-\*/%])', 'Operator'),
	(r'([^\^_\+\-\*/%]*)', 'Plaintext')
]

# Tokens that disable text parsing : Until this is encountered, yield this token
disabling_tokens = {
	'CodeInline_AMB': ('`', 'Plaintext'),
    'MathInline_OPEN': ('»', 'Math')
}

text_tokens = [(compile(exp, flags=re_flags), val) for (exp, val) in text_tokens]


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


def get_text_tokens(text):
	disabled = False
	enabling_char = ''
	disabled_token = ''
	while text:

		if disabled:
			m = match(r'[^%s]*' % enabling_char, text)
			yield disabled_token, m.group(0)

			text = text[len(m.group(0)):]
			disabled = False
		else:
			for exp, val in text_tokens:
				m = match(exp, text)

				if m:
					m_len = len(m.group(0))

					if val in disabling_tokens:
						disabled = True
						enabling_char, disabled_token = disabling_tokens[val]

					yield val, m.group(0)

					text = text[m_len:]
					break
			else:
				raise Exception("Unrecognized token at %s" % text[:50])


def get_math_tokens(text):
	while text:
		for exp, val in math_tokens:
			m = match(exp, text)

			if m:
				m_len = len(m.group(0))

				yield val, m.group(1)

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


def block_is_math(block):
	return match(re_math_open, block[0]) and match(re_math_close, block[-1])


def ulist_item_text(item):
	return sub(re_ulistitem, '', item)


def olist_item_text(item):
	return sub(re_olistitem, '', item)