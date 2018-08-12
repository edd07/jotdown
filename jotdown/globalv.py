import os
from collections import OrderedDict
import re
import mimetypes
import typing

references = OrderedDict()  # References for citation mode
html_document_ids = set()  # Set of strings that are ids to certain html elements

re_flags = re.UNICODE

# Custom types for clearer type hinting
Block = typing.List[str]


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
			raise UnicodeEncodeError('Document contains characters with Unicode codepoints greater that 65536, not supported by RTF')
	return ''.join(res)


def read_with_encoding(fname: str, encoding=None) -> str:
	"""
	Returns the context of a file of unknown encoding, hopefully.
	"""
	# TODO: Avoid having to read the whole file into memory

	# Explicit encoding
	if encoding:
		with open(fname, encoding=encoding) as f:
			if __debug__: print(f'Reading {fname} with {encoding}')
			return f.read()

	# If chardet is installed, use it
	try:
		from chardet import detect
		with open(fname, 'rb') as f:
			raw_data = f.read()
			guessed_encoding = detect(raw_data)['encoding']
			if __debug__: print(f'Reading {fname} with chardet, encoding is {guessed_encoding}')
			return str(raw_data, encoding=guessed_encoding)
	except ImportError:
		pass

	# Guess
	try:
		with open(fname, encoding='utf-8') as f:  # Is it a sane system?
			if __debug__: print(f'Trying to read {fname} with utf-8')
			return f.read()
	except UnicodeDecodeError:
		pass

	try:
		with open(fname, encoding='cp1252') as f:  # Is it Windows?
			if __debug__: print(f'Trying to read {fname} with cp1252')
			return f.read()
	except UnicodeDecodeError:
		pass

	try:
		with open(fname, encoding='mac_roman') as f:  # Is it Mac?
			if __debug__: print(f'Trying to read {fname} with mac_roman')
			return f.read()
	except UnicodeDecodeError:
		pass

	try:
		with open(fname) as f:  # Try default encoding
			if __debug__: print(f'Trying to read {fname} with your system\'s default encoding. Godspeed.')
			return f.read()
	except UnicodeDecodeError:
		raise Exception(f'Could not open {fname}, unknown encoding')

