import os
from collections import OrderedDict
import re
import mimetypes

references = OrderedDict()  # References for citation mode
html_document_ids = set()  # Set of strings that are ids to certain html elements

re_flags = re.UNICODE


def content_filetypes(fname):
	guessed_type = mimetypes.guess_type(fname)
	if guessed_type[0] is None:
		return None
	mtype, msubtype = guessed_type[0].split('/')
	if mtype in ('image', 'audio', 'video'):
		return mtype
	elif msubtype == 'x-shockwave-flash':
		return 'flash'


def ext_translation(url, fformat):
	name, ext = os.path.splitext(url)
	if ext == '.jd':
		url = name + '.' + fformat
	return url
