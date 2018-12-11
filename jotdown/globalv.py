import logging
import os
from collections import OrderedDict
import re
import mimetypes
import typing

from errors import EncodingException

references = OrderedDict()  # References for citation mode
html_document_ids = set()  # Set of strings that are ids to certain html elements

re_flags = re.UNICODE

# Custom types for clearer type hinting
Block = typing.List[str]

style_ext = {
	# Output format: extension of "stylesheet" file
	'html': '.css',
	'rtf': '.rtf',
	'latex': '.tex',
	'debug': '',
	'jd': '',
}

known_encodings = {
	'.debug': 'utf-8',
	'.rtf': 'ascii',
}

explicit_encodings = {
	# File extension: RE of how to find its explicit encoding
	'.css': re.compile(rb'^@charset "([\w-]+)";'),
	'.html': re.compile(rb'.*<meta\s[^>]*\scharset=[\'"]([\w-]+)[\'"]\s*[^>]*/\s*>'),  # TODO: accepts mismatching quotes
	'.tex': re.compile(rb'.*\\usepackage\[([\w-]+)\]{inputenc}'),
}


def content_filetypes(fname: str) -> typing.Optional[str]:
	guessed_type = mimetypes.guess_type(fname)[0]
	if guessed_type is None:
		return None
	mtype, msubtype = guessed_type.split('/')
	if mtype in ('image', 'audio', 'video'):
		return mtype
	elif msubtype == 'x-shockwave-flash':
		return 'flash'


def ext_translation(url: str, fformat: str) -> str:
	if '#' in url:
		url, anchor = url.split('#', 1)
	else:
		anchor = None

	name, ext = os.path.splitext(url)
	if ext == '.jd':
		url = name + '.' + fformat

	if anchor:
		return url + '#' + anchor
	else:
		return url


def rtf_escape_unicode(string: str) -> str:
	res = []
	for char in string:
		cp = ord(char)
		if cp < 128 and char not in r'\{}':
			res.append(char)
		elif cp < 256:
			# \'xy syntax, with xy as a hex number
			res.extend(r"\'%02x" % cp)
		elif cp < 32768:
			# \uN? syntax, with N as a decimal
			res.extend(r'\uc1\u%d?' % cp)
		elif cp < 65536:
			# \uN? syntax, with N as a decimal, negative number
			res.extend(r'\uc1\u%d?' % (cp - 65536))
		else:
			raise EncodingException(
				'Document contains characters with Unicode codepoints greater that 65536, not supported by RTF'
			)
	return ''.join(res)


def read_with_encoding(path: str) -> str:
	"""
	Returns the contents of a file of unknown encoding, hopefully.
	"""
	# TODO: Avoid having to read the whole file into memory

	fname, ext = os.path.splitext(path)
	encoding = None

	# Known encodings
	if ext in known_encodings:
		encoding = known_encodings[ext]
		logging.info(f'Reading {path} with known encoding {encoding}')

	# Encoding could be explicitly announced in the file
	elif ext in explicit_encodings:
		with open(path, 'rb') as f:
			head = f.read(1024)
		m = explicit_encodings[ext].match(head)
		if m:
			encoding = str(m.group(1), encoding='ascii')
			logging.info(f'Reading {path} with explicit encoding {encoding}')

	if encoding:
		with open(path, encoding=encoding) as f:
			return f.read()

	# If chardet is installed, use it
	try:
		from chardet import detect
	except ImportError:
		pass
	else:
		with open(path, 'rb') as f:
			raw_data = f.read()
			guessed_encoding = detect(raw_data)['encoding']
			logging.info(f'Reading {path} with chardet\'d encoding {guessed_encoding}')
			return str(raw_data, encoding=guessed_encoding)
	# Guess
	try:
		with open(path, encoding='utf-8') as f:  # Is it a sane system?
			logging.info(f'Trying to read {path} with utf-8')
			return f.read()
	except UnicodeDecodeError:
		pass

	try:
		with open(path, encoding='cp1252') as f:  # Is it Windows?
			logging.info(f'Trying to read {path} with cp1252')
			return f.read()
	except UnicodeDecodeError:
		pass

	try:
		with open(path, encoding='mac_roman') as f:  # Is it Mac?
			logging.info(f'Trying to read {path} with mac_roman')
			return f.read()
	except UnicodeDecodeError:
		pass

	try:
		with open(path) as f:  # Try default encoding
			logging.info(f'Trying to read {path} with your system\'s default encoding. Godspeed.')
			return f.read()
	except UnicodeDecodeError:
		raise EncodingException(f'Could not open {path}, unknown encoding')
