# -*- coding: utf-8 -*-
import string
from re import sub, compile, match, UNICODE

from jotdown.roman import fromRoman, InvalidRomanNumeralError
from jotdown.regex import *

# Init RE objects
re_flags = UNICODE
re_ulistitem = compile(r'^(\t*)[\*\-\+]\s+', flags=re_flags)
re_olistitem = compile(r'^(\t*)(\w+)\.\s+', flags=re_flags)
re_code_amb = compile(r'^```\s*$', flags=re_flags)
re_code_open = compile(r'^```([\w\d+#][\w\d+#\s]*)$', flags=re_flags)
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

	(r'~~', 'Strikethrough_AMB'),

	(r'«', 'MathInline_OPEN'),
	(r'»', 'MathInline_CLOSE'),

	(r'!\[([^\]]*)\]\(([^\)\s]*)\s*(?:"([^"]*)"\s*)?\)', 'Image'),
	(r'(https?://\S+)', 'ImplicitLink'),
	(r'\[([^\]]*)\]\(([^\)]*)\)', 'Link'),

	(r'\[([^\]]*)\]\[([^\]]*)\]', 'ReferenceLink'),
	(r'\[([^\]]*)\]:\s*(.*)\n', 'ReferenceDef'),

	(r'(\S+@\S+\.\S+)', 'ImplicitEmail'),

	(r'(\s*(?:[^\s_\*`«»~]|~(?!~)|\\[^_\*`«»~]|(?<=[^\W_])_(?=[^\W_]))*\s*)', 'Plaintext')

]

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

	(r'#\s*([^#\n]*)(?:#|\n|$)', 'Comment'),
	(r'_([%(num)s]+|[^%(not_id)s]+)' % math_exp, 'Subscript'),
	(r'\^([%(num)s]+|[^%(not_id)s]+|\*|∁|)' % math_exp, 'Superscript'),
	(r'([+−]?[%(num)s][%(num)s\.]*)' % math_exp, 'Number'),
	(r'([%(op)s])' % math_exp, 'Operator'),
	# (r'([^_\^%(op)]*)\s*', 'Plaintext'),
	(r'([+−]?[^%(not_id)s]+)' % math_exp, 'Identifier'),
	(r'([^\S\n]+)', 'Whitespace'),
	(r'(\n)', 'Newline')
]

bracket_closable = ["SubscriptBrackets", "SuperscriptBrackets", "Sum", "Prod", "Int"]

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

		if match(re_code_open, line):
			in_blankable_block = True
		elif match(re_code_amb, line):
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


def block_is_horizontal_rule(block):
	if len(block) > 1:
		return False
	line = block[0].replace(' ', '').replace('\t', '')
	for symbol in '*-':
		for char in line:
			if char != symbol and char != '\n':
				break
		else:
			return True
	return False


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
		if re_ulistitem.match(line):
			continue
		m = re_olistitem.match(line)
		if m:
			if lex_olist(m):
				continue
		return False
	return True


def block_is_code(block):
	return (match(re_code_open, block[0]) or match(re_code_amb, block[0])) and match(re_code_amb, block[-1])


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


def block_is_blockquote(block):
	return block[0][0] == '>'


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


def lex_olist(m):
	"""Attempt to parse a numeral on the list item, be it decimal, roman or alphabetical"""
	# TODO: support for non-latin alphabet numbering? HTML doesn't seem to support it
	_, numeral = m.groups()

	try:
		return '1', int(numeral)  # is it an integer?
	except ValueError:
		try:
			value = fromRoman(numeral.upper())  # is it a roman numeral?
			case = 'i' if numeral.lower() == numeral else 'I'
			return case, value
		except InvalidRomanNumeralError:
			value = 0  # is it just a letter?
			for char in numeral:
				if char not in string.ascii_letters:
					return None
				value = value * 26 + (string.ascii_lowercase.index(char.lower()) + 1)
			case = 'a' if numeral.lower() == numeral else 'A'
			return case, value
