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

math_exp = {
	'op': r"\+\-\*/%=↔→←~≈≠≟<≤≥>∈∉⊂⊄⊆⊈…!",
    'num': r'\d',
    'not_id': r'\W_',
    'parens': r'\(\)\{\}\[\]'
}

math_tokens = [
	(r'(\^\()', "SuperscriptParens_OPEN"),
    (r'(_\()', "SubscriptParens_OPEN"),
	(r'(\()', "Parenthesis_OPEN"),
    (r'(\))', "Parenthesis_CLOSE"),
	(r'({)', "Braces_OPEN"),
	(r'(})', "Braces_CLOSE"),
    (r'(\[)', "Brackets_OPEN"),
	(r'(\])', "Brackets_CLOSE"),

	(r'#\s*([^#\n]*)[#\n$]', 'Comment'),
	(r'_([^%(not_id)s]+|[%(num)s]+)' % math_exp, 'Subscript'),
    (r'\^([^%(not_id)s]+|[%(num)s]+)' % math_exp, 'Superscript'),
	(r'([%(op)s])' % math_exp, 'Operator'),
	(r'(%(num)s[%(num)s\.]*)' % math_exp, 'Number'),
	#(r'([^_\^%(op)]*)\s*', 'Plaintext'),
    (r'([^%(not_id)s]+)' % math_exp, 'Identifier'),
	(r'([^\S\n]+)', 'Whitespace'),
	(r'(\n)', 'Newline')
]

parens_closable = ["SubscriptParens", "SuperscriptParens"]

math_subst = [
(r"ALPHA", 'Α'),
(r"BETA", 'Β'),
(r"GAMMA", 'Γ'),
(r"DELTA", 'Δ'),
(r"EPSILON", 'Ε'),
(r"ZETA", 'Ζ'),
(r"[^ZH]ETA", 'Η'),  # TODO, Change to lookbehind
(r"THETA", 'Θ'),
(r"IOTA", 'Ι'),
(r"KAPPA", 'Κ'),
(r"LAMBDA", 'Λ'),
(r"MU", 'Μ'),
(r"NU", 'Ν'),
(r"XI", 'Ξ'),
(r"OMICRON", 'Ο'),
(r"PI", 'Π'),
(r"RHO", 'Ρ'),
(r"SIGMA", 'Σ'),
(r"TAU", 'Τ'),
(r"YPSILON", 'Υ'),
(r"PHI", 'Φ'),
(r"CHI", 'Χ'),
(r"PSI", 'Ψ'),
(r"OMEGA", 'Ω'),
(r"alpha", 'α'),
(r"beta", 'β'),
(r"gamma", 'γ'),
(r"delta", 'δ'),
(r"epsilon", 'ε'),
(r"zeta", 'ζ'),
(r"eta", 'η'),  # TODO, Change to lookbehind
(r"theta", 'θ'),
(r"iota", 'ι'),
(r"kappa", 'κ'),
(r"lambda", 'λ'),
(r"mu", 'μ'),
(r"nu", 'ν'),
(r"xi", 'ξ'),
(r"omicron", 'ο'),
(r"pi", 'π'),
(r"rho", 'ρ'),
(r"sigma", 'σ'),
(r"tau", 'τ'),
(r"ypsilon", 'υ'),
(r"phi", 'φ'),
(r"chi", 'χ'),
(r"psi", 'ψ'),
(r"omega", 'ω'),

(r"<->", '↔'),
(r"->", '→'),
(r"<-", '←'),
(r"~=", '≈'),
(r"~", '∼'),
(r"!=", '≠'),
(r"\?=", '≟'),
(r"<=", '≤'),
(r">=", '≥'),
(r"€", '∈'),
(r"!€", '∉'),
(r"¢=", '⊆'),
(r"!¢=", '⊈'),
(r"¢", '⊂'),
(r"!¢", '⊄'),
(r"\.\.\.", '…')
]

# Tokens that disable text parsing : Until this is encountered, yield this token
disabling_tokens = {
	'CodeInline_AMB': ('`', 'Plaintext', 'CodeInline_AMB'),
    'MathInline_OPEN': ('»', 'Math', 'MathInline_CLOSE')
}

text_tokens = [(compile(exp, flags=re_flags), val) for (exp, val) in text_tokens]
math_tokens = [(compile(exp, flags=re_flags), val) for (exp, val) in math_tokens]

math_subst = [(compile(exp, flags=re_flags), val) for (exp, val) in math_subst]


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
	closing_token = ''
	while text:

		if disabled:
			m = match(r'([^%s]*)%s' % (enabling_char, enabling_char), text)
			if not m:
				raise Exception("Expected '%s' for unclosed tag in %s" % (enabling_char, repr(text[:50])))

			yield disabled_token, m.group(1)
			yield closing_token, enabling_char

			text = text[len(m.group(0)):]
			disabled = False
		else:
			for exp, val in text_tokens:
				m = match(exp, text)

				if m:
					m_len = len(m.group(0))

					if val in disabling_tokens:
						disabled = True
						enabling_char, disabled_token, closing_token = disabling_tokens[val]

					yield val, m.group(0)
					text = text[m_len:]
					break
			else:
				raise Exception("Unrecognized token at %s" % repr(text[:50]))


def get_math_tokens(text):
	while text:
		for exp, val in math_tokens:
			m = match(exp, text)

			if m:
				m_len = len(m.group(0))

				if val != 'Whitespace':
					yield val, m.group(1)

				text = text[m_len:]
				break
		else:
			raise Exception("Unrecognized math token at %s" % repr(text[:50]))


def replace_math(text):
	for k, v in math_subst:
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