"""
Classes and helper functions to report errors usefully.
"""

token_names = {
	# Token name: (human-readable name, token, token pair)
	'CodeInline_AMB': ('inline code', '`', '`'),

	'StrongEmph_A_AMB': ('bold italics', '***', '***'),
	'StrongEmph_B_AMB': ('bold italics', '___', '___'),

	'Strong_A_AMB': ('bold', '**', '**'),
	'Strong_B_AMB': ('bold', '__', '__'),

	'Emph_A_AMB': ('italics', '*', '*'),
	'Emph_B_AMB': ('italics', '_', '_'),

	'Strikethrough_AMB': ('strikethrough', '~~', '~~'),

	'MathInline_OPEN': ('inline math', '«', '»'),
	'MathInline_CLOSE': ('inline math', '»', '«'),
}


class LineNumberException(Exception):
	"""
	Class that stores a line number of when it happened
	"""
	def __init__(self, line_number: int, message: str) -> None:
		super().__init__(message)
		self.line_number = line_number


class ContextException(LineNumberException):
	"""
	Class that stores a fragment of jotdown code to give context to the error
	"""
	def __init__(self, line_number: int, message: str, context: str) -> None:
		super().__init__(line_number, message)
		self.context = summary(context)


class MissingTagException(LineNumberException):
	"""
	Class that stores which tag is missing and, optionally, which one was encountered instead
	"""
	def __init__(
			self,
			line_number: int,
			unpaired_tag: str,
			*,
			encountered_tag: str = None,
			opening: bool = False
	) -> None:
		tag_type = 'opening' if opening else 'closing'
		encountered_tag = token_names[encountered_tag] if encountered_tag else None
		if encountered_tag:
			message = f'Expected {tag_type} tag for'
		else:
			message = f'Missing {tag_type} tag for'
		super().__init__(line_number, message)
		self.unpaired_tag = token_names[unpaired_tag]
		self.encountered_tag = encountered_tag


class EncodingException(Exception):
	pass


def summary(text: str, length: int = 50):
	text = text.split('\n')[0]  # Math strings could have newlines in them?
	if len(text) > length:
		return f'{text[:length]}...'
	else:
		return text
