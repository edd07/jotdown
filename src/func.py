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
	(r'#\s*([^#\n$]*)[#\n$]', 'Comment'),
	(r'\B_(\w+)\s*', 'Subscript'),
    (r'\B\^(\w+)\s*', 'Superscript'),
	(r'\b([^\W_\d]+)\s*', 'Identifier'),
	(r'([\+\-\*/%=↔→←≈≠≤≥])\s*', 'Operator'),
	(r'([^\s\^_\+\-\*/%]*)\s*', 'Plaintext')
]

math_subst = {
"ALPHA": 'Α',
"BETA": 'Β',
"GAMMA": 'Γ',
"DELTA": 'Δ',
"EPSILON": 'Ε',
"ZETA": 'Ζ',
"[^ZH]ETA": 'Η',
"THETA": 'Θ',
"IOTA": 'Ι',
"KAPPA": 'Κ',
"LAMBDA": 'Λ',
"MU": 'Μ',
"NU": 'Ν',
"XI": 'Ξ',
"OMICRON": 'Ο',
"PI": 'Π',
"RHO": 'Ρ',
"SIGMA": 'Σ',
"TAU": 'Τ',
"YPSILON": 'Υ',
"PHI": 'Φ',
"CHI": 'Χ',
"PSI": 'Ψ',
"OMEGA": 'Ω',
"alpha": 'α',
"beta": 'β',
"gamma": 'γ',
"delta": 'δ',
"epsilon": 'ε',
"zeta": 'ζ',
"eta": 'η',
"theta": 'θ',
"iota": 'ι',
"kappa": 'κ',
"lambda": 'λ',
"mu": 'μ',
"nu": 'ν',
"xi": 'ξ',
"omicron": 'ο',
"pi": 'π',
"rho": 'ρ',
"sigma": 'σ',
"tau": 'τ',
"ypsilon": 'υ',
"phi": 'φ',
"chi": 'χ',
"psi": 'ψ',
"omega": 'ω',

"<->": '↔',
"->": '→',
"<-": '←',
"~=": '≈',
"~": '∼',
"!=": '≠',
"<=": '≤',
">=": '≥'

}

# Tokens that disable text parsing : Until this is encountered, yield this token
disabling_tokens = {
	'CodeInline_AMB': ('`', 'Plaintext'),
    'MathInline_OPEN': ('»', 'Math')
}

text_tokens = [(compile(exp, flags=re_flags), val) for (exp, val) in text_tokens]
math_tokens = [(compile(exp, flags=re_flags), val) for (exp, val) in math_tokens]

math_subst = {compile(exp, flags=re_flags): val for (exp, val) in math_subst.items()}


def get_blocks(file):
	block = []
	in_blankable_block = False
	for line in file:

		if match(re_code_delim, line):
			in_blankable_block = not in_blankable_block
		elif match(re_math_open, line):
			in_blankable_block = True
		elif match(re_math_close, line):
			in_blankable_block = False

		if not line.strip() and not in_blankable_block:
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


def replace_math(text):
	for k, v in math_subst.items():
		text = sub(k, v, text)

	return text


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