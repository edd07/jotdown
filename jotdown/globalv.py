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


def content_filetypes(fname: str) -> str:
	guessed_type = mimetypes.guess_type(fname)
	if guessed_type[0] is None:
		return None
	mtype, msubtype = guessed_type[0].split('/')
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
			raise Exception('Document contains characters with Unicode codepoints greater that 65536, not supported by RTF')
	return ''.join(res)

