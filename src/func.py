# -*- coding: utf-8 -*-
from re import sub, compile, match, UNICODE

# Init RE objects
re_flags = UNICODE
re_listitem = compile(r'^(\t*)([\*\-\+]|\d+\.)\s+')
re_ulistitem = compile(r'^(\t*)[\*\-\+]\s+', flags=re_flags)
re_olistitem = compile(r'^(\t*)(\d+)\.\s+', flags=re_flags)
re_code_delim = compile(r'^```\s*$', flags=re_flags)
re_math_open = compile(r'^«««\s*$', flags=re_flags)
re_math_close = compile(r'^»»»\s*$', flags=re_flags)

# Token definitions for text parsing

text_tokens = [
	(r'`', 'CodeInline_AMB'),

	(r'\*\*\*', 'StrongEmph_AMB'),
    (r'\b___', 'StrongEmph_AMB'),

    (r'\*\*', 'Strong_AMB'),
    (r'\b__', 'Strong_AMB'),

    (r'\*', 'Emph_AMB'),
    (r'\b_', 'Emph_AMB'),

    (r'«', 'MathInline_OPEN'),
    (r'»', 'MathInline_CLOSE'),

    (r'(https?://\S*)', 'ImplicitLink'),
    (r'\[([^)]*)\]\(([^\[]*)\)', 'Link'),

    (r'(\S*@\S*)', 'ImplicitEmail'),

	(r'(\s*(?:[^\s_\*`«»]|\\[^_\*`«»]|(?<=[^\W_])_(?=[^\W_]))*\s*)', 'Plaintext')

]

math_exp = {
	'op': r"\+\*/%=↔→←≈∼≠≟<≤≥>∴∈∉⊂⊄⊆⊈…!±−,:|∀∧∨⊕¬",
    'num': r'\d∞',
    'not_id': r'\W_',
    'not_letter': r'\W\d_',
    'parens': r'\(\)\{\}\[\]'
}

math_tokens = [
	(r'(\^\[)', "SuperscriptBrackets_OPEN"),
    (r'(_\[)', "SubscriptBrackets_OPEN"),
    (r'(sum\[)', "Sum_OPEN"),
    (r'(prod\[)', "Prod_OPEN"),
    (r'(int\[)', "Int_OPEN"),
	(r'(\()', "Parenthesis_OPEN"),
    (r'(\))', "Parenthesis_CLOSE"),
	(r'({)', "Braces_OPEN"),
	(r'(})', "Braces_CLOSE"),
    (r'(\[)', "Brackets_OPEN"),  # Brackets are for grouping that won't show up in output
	(r'(\])', "Brackets_CLOSE"),

	(r'#\s*([^#\n]*)(?:[#\n]|$)', 'Comment'),
	(r'_([^%(not_id)s]+|[%(num)s]+)' % math_exp, 'Subscript'),
    (r'\^([^%(not_id)s]+|[%(num)s]+|\*|∁)' % math_exp, 'Superscript'),
	(r'([+−]?[%(num)s][%(num)s\.]*)' % math_exp, 'Number'),
    (r'([%(op)s])' % math_exp, 'Operator'),
	#(r'([^_\^%(op)]*)\s*', 'Plaintext'),
    (r'([+−]?[^%(not_id)s]+)' % math_exp, 'Identifier'),
	(r'([^\S\n]+)', 'Whitespace'),
	(r'(\n)', 'Newline')
]

bracket_closable = ["SubscriptBrackets", "SuperscriptBrackets", "Sum", "Prod", "Int"]


math_subst = [
# Greek alphabet
(r"(?:\b|(?<=[%(not_letter)s]))ALPHA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Α'),
(r"(?:\b|(?<=[%(not_letter)s]))BETA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Β'),
(r"(?:\b|(?<=[%(not_letter)s]))GAMMA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Γ'),
(r"(?:\b|(?<=[%(not_letter)s]))DELTA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Δ'),
(r"(?:\b|(?<=[%(not_letter)s]))EPSILON(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ε'),
(r"(?:\b|(?<=[%(not_letter)s]))ZETA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ζ'),
(r"(?:\b|(?<=[%(not_letter)s]))ETA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Η'),
(r"(?:\b|(?<=[%(not_letter)s]))THETA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Θ'),
(r"(?:\b|(?<=[%(not_letter)s]))IOTA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ι'),
(r"(?:\b|(?<=[%(not_letter)s]))KAPPA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Κ'),
(r"(?:\b|(?<=[%(not_letter)s]))LAMBDA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Λ'),
(r"(?:\b|(?<=[%(not_letter)s]))MU(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Μ'),
(r"(?:\b|(?<=[%(not_letter)s]))NU(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ν'),
(r"(?:\b|(?<=[%(not_letter)s]))XI(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ξ'),
(r"(?:\b|(?<=[%(not_letter)s]))OMICRON(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ο'),
(r"(?:\b|(?<=[%(not_letter)s]))PI(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Π'),
(r"(?:\b|(?<=[%(not_letter)s]))RHO(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ρ'),
(r"(?:\b|(?<=[%(not_letter)s]))SIGMA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Σ'),
(r"(?:\b|(?<=[%(not_letter)s]))TAU(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Τ'),
(r"(?:\b|(?<=[%(not_letter)s]))YPSILON(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Υ'),
(r"(?:\b|(?<=[%(not_letter)s]))PHI(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Φ'),
(r"(?:\b|(?<=[%(not_letter)s]))CHI(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Χ'),
(r"(?:\b|(?<=[%(not_letter)s]))PSI(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ψ'),
(r"(?:\b|(?<=[%(not_letter)s]))OMEGA(?:\b|(?=[%(not_letter)s]))" % math_exp, 'Ω'),
(r"(?:\b|(?<=[%(not_letter)s]))alpha(?:\b|(?=[%(not_letter)s]))" % math_exp, 'α'),
(r"(?:\b|(?<=[%(not_letter)s]))beta(?:\b|(?=[%(not_letter)s]))" % math_exp, 'β'),
(r"(?:\b|(?<=[%(not_letter)s]))gamma(?:\b|(?=[%(not_letter)s]))" % math_exp, 'γ'),
(r"(?:\b|(?<=[%(not_letter)s]))delta(?:\b|(?=[%(not_letter)s]))" % math_exp, 'δ'),
(r"(?:\b|(?<=[%(not_letter)s]))epsilon(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ε'),
(r"(?:\b|(?<=[%(not_letter)s]))zeta(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ζ'),
(r"(?:\b|(?<=[%(not_letter)s]))eta(?:\b|(?=[%(not_letter)s]))" % math_exp, 'η'),
(r"(?:\b|(?<=[%(not_letter)s]))theta(?:\b|(?=[%(not_letter)s]))" % math_exp, 'θ'),
(r"(?:\b|(?<=[%(not_letter)s]))iota(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ι'),
(r"(?:\b|(?<=[%(not_letter)s]))kappa(?:\b|(?=[%(not_letter)s]))" % math_exp, 'κ'),
(r"(?:\b|(?<=[%(not_letter)s]))lambda(?:\b|(?=[%(not_letter)s]))" % math_exp, 'λ'),
(r"(?:\b|(?<=[%(not_letter)s]))mu(?:\b|(?=[%(not_letter)s]))" % math_exp, 'μ'),
(r"(?:\b|(?<=[%(not_letter)s]))nu(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ν'),
(r"(?:\b|(?<=[%(not_letter)s]))xi(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ξ'),
(r"(?:\b|(?<=[%(not_letter)s]))omicron(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ο'),
(r"(?:\b|(?<=[%(not_letter)s]))pi(?:\b|(?=[%(not_letter)s]))" % math_exp, 'π'),
(r"(?:\b|(?<=[%(not_letter)s]))rho(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ρ'),
(r"(?:\b|(?<=[%(not_letter)s]))sigma(?:\b|(?=[%(not_letter)s]))" % math_exp, 'σ'),
(r"(?:\b|(?<=[%(not_letter)s]))tau(?:\b|(?=[%(not_letter)s]))" % math_exp, 'τ'),
(r"(?:\b|(?<=[%(not_letter)s]))ypsilon(?:\b|(?=[%(not_letter)s]))" % math_exp, 'υ'),
(r"(?:\b|(?<=[%(not_letter)s]))phi(?:\b|(?=[%(not_letter)s]))" % math_exp, 'φ'),
(r"(?:\b|(?<=[%(not_letter)s]))chi(?:\b|(?=[%(not_letter)s]))" % math_exp, 'χ'),
(r"(?:\b|(?<=[%(not_letter)s]))psi(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ψ'),
(r"(?:\b|(?<=[%(not_letter)s]))omega(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ω'),

# Number sets
(r'(?:\b|(?<=[%(not_letter)s]))NATURALS(?:\b|(?=[%(not_letter)s]))' % math_exp, 'ℕ'),
(r'(?:\b|(?<=[%(not_letter)s]))INTEGERS(?:\b|(?=[%(not_letter)s]))' % math_exp, 'ℤ'),
(r'(?:\b|(?<=[%(not_letter)s]))RATIONALS(?:\b|(?=[%(not_letter)s]))' % math_exp, 'ℚ'),
(r'(?:\b|(?<=[%(not_letter)s]))REALS(?:\b|(?=[%(not_letter)s]))' % math_exp, 'ℝ'),
(r'(?:\b|(?<=[%(not_letter)s]))COMPLEX(?:\b|(?=[%(not_letter)s]))' % math_exp, 'ℂ'),

# Infinities
(r"(?:\b|(?<=[%(not_letter)s]))INF(?:\b|(?=[%(not_letter)s]))" % math_exp, '∞'),
(r"(?:\b|(?<=[%(not_letter)s]))ALEPH(?:\b|(?=[%(not_letter)s]))" % math_exp, 'ℵ'),

# Logic
(r"(?:\b|(?<=[%(not_letter)s]))AND(?:\b|(?=[%(not_letter)s]))" % math_exp, '∧'),
(r"(?:\b|(?<=[%(not_letter)s]))OR(?:\b|(?=[%(not_letter)s]))" % math_exp, '∨'),
(r"(?:\b|(?<=[%(not_letter)s]))XOR(?:\b|(?=[%(not_letter)s]))" % math_exp, '⊕'),

# Relation operators
(r"<->", '↔'),
(r"->", '→'),
(r"<-", '←'),
(r"~=", '≈'),
(r"~", '∼'),
(r"!=", '≠'),
(r"\?=", '≟'),
(r"<=", '≤'),
(r">=", '≥'),
(r":\.", '∴'),

# Sets
(r"€", '∈'),
(r"!€", '∉'),
(r"©=", '⊆'),
(r"!©=", '⊈'),
(r"©", '⊂'),
(r"!©", '⊄'),
(r"ø", '∅'),
(r"[Ĉĉ]", "^∁"),
(r"(?:\b|(?<=[%(not_letter)s]))UNION(?:\b|(?=[%(not_letter)s]))" % math_exp, '∪'),
(r"(?:\b|(?<=[%(not_letter)s]))INTERSECTION(?:\b|(?=[%(not_letter)s]))" % math_exp, '∩'),

# More operators
(r"\.\.\.", '…'),
(r"\+-", '±'),
(r"-", '−'),

# Quantification
(r"(?:\b|(?<=[%(not_letter)s]))FORALL(?:\b|(?=[%(not_letter)s]))" % math_exp, '∀'),
(r"(?:\b|(?<=[%(not_letter)s]))!EXISTS(?:\b|(?=[%(not_letter)s]))" % math_exp, '∄'),
(r"(?:\b|(?<=[%(not_letter)s]))EXISTS(?:\b|(?=[%(not_letter)s]))" % math_exp, '∃')
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

			yield disabled_token, m.groups()
			yield closing_token, (enabling_char,)

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

					yield val, m.groups()
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


def block_is_list(block):
	for line in block:
		if not match(re_listitem, line):
			return False
	return True


def block_is_code(block):
	return match(re_code_delim, block[0]) and match(re_code_delim, block[-1])


def block_is_math(block):
	return match(re_math_open, block[0]) and match(re_math_close, block[-1])


def block_is_md_table(block):
	table_cols = len(block[0].split('|'))

	if table_cols < 2:
		return False

	for line in block:
		row_cols = len(line.split('|'))

		if row_cols != table_cols:
			return False
	return True


def list_item_text(item):
	if match(re_olistitem, item):
		return sub(re_olistitem, '', item)
	return sub(re_ulistitem, '', item)


def cell_align(cell):
	if cell.endswith('-'):
		return 0  # Left
	elif cell.startswith('-'):
		return 2  # Right
	else:
		return 1  # Center