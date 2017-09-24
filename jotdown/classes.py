# -*- coding: utf-8 -*-
import html
import os
import re
from getpass import getuser
from socket import gethostname

import jotdown.globalv as globalv
from jotdown.regex import latex_math_subst


# Abstract ---------------------------------
class Node:
	def __init__(self, children=None):
		self.children = children if children else []

	def emit_html(self, **kwargs):
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs):
		return ''.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs):
		return ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_debug(self, indent=0, **kwargs):
		return ('\t' * indent) + type(self).__name__ + '\n' + ''.join(i.emit_debug(indent + 1, **kwargs) for i in self.children)

	def emit_jd(self, **kwargs):
		return ''.join(i.emit_jd(**kwargs) for i in self.children)


class TextNode(Node):
	def __init__(self, text):
		super().__init__()
		self.text = text

	def emit_html(self, **kwargs):
		return html.escape(self.text, quote=True)

	def emit_rtf(self, **kwargs):
		return globalv.rtf_escape_unicode(self.text)

	def emit_latex(self, **kwargs):
		special_chars = (
			('\\', r'\textbackslash '),
		    ('&', r'\& '),
		    ('%', r'\%'),
		    ('$', r'\$'),
		    ('#', r'\#'),
		    ('_', r'\_'),
		    ('{', r'\{'),
		    ('}', r'\}'),
		    ('~', r'\textasciitilde '),
		    ('^', r'\textasciicircum '),
			('—', r'---'),
			('–', r'--'),
			('>', r'\textgreater '),
			('<', r'\textless '),
		)
		text = self.text
		for old, new in special_chars:
			text = text.replace(old, new)
		return text

	def emit_debug(self, indent=0, **kwargs):
		summary = repr(self.text[:50])
		if len(self.text) > len(summary):
			summary += '...'
		res = ('\t' * indent) + type(self).__name__ + ' ' + summary + '\n'
		res += ''.join(i.emit_debug(indent + 1, **kwargs) for i in self.children)
		return res

	def emit_jd(self, **kwargs):
		return self.text


# For blocks -------------------------------------------------------------------------


class Document(Node):
	def __init__(self, children=None, name="Jotdown Document", author=None):
		super().__init__(children)
		self.name = name
		self.author = getuser() if not author else author
		self.hostname = gethostname()

	def emit_html(self, stylesheet, ref_style=False, embed_css=True, **kwargs):
		if embed_css:
			with open(stylesheet) as css:
				css_string = '<style>%s</style>' % css.read()
		else:
			css_string = '<link rel="stylesheet" href="%s"/>' % stylesheet

		res = '<!DOCTYPE html><html><head><title>%s</title><meta charset="UTF-8">%s</head><body>'\
		      % (self.name, css_string)
		res += '\n'.join(block.emit_html(ref_style=ref_style, **kwargs) for block in self.children)
		if ref_style:
			res += '<footer>' + ReferenceList().emit_html(ref_style=True, **kwargs) + '</footer>'
		res += '</body></html>'
		# TODO: Author and creation time meta tags
		return res

	def emit_rtf(self, stylesheet, **kwargs):
		with open(stylesheet) as f_style:
			tables = f_style.read()
		# TODO: Author in info, and create time
		return r'''{\rtf1\ansi\deff0\widowctrl %s
{\info
{\title %s}
{\author PLACEHOLDER}
{\creatim\yr2016\mo7\dy20\hr18\min37}
}
''' % (tables, self.name) + ''.join(block.emit_rtf(**kwargs) for block in self.children) + '}'

	def emit_latex(self, stylesheet, ref_style=False, **kwargs):
		packages = r'''
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{csquotes}
'''
		field_dict = {
			'packages': packages,
			'title': self.name,
			'body': ''.join(block.emit_latex(ref_style=ref_style, **kwargs) for block in self.children),
			'references': ReferenceList().emit_latex(ref_style=True, **kwargs) if ref_style else '',
			'author': self.author,
			'institution': self.hostname,
		}
		with open(stylesheet) as f_style:
			return f_style.read() % field_dict


class Heading(Node):
	def __init__(self, level, children=None):
		super().__init__(children)
		self.level = min(level, 6)

	def emit_html(self, **kwargs):
		# Sanitize the text for the id
		ident = ''.join(i.emit_html(**kwargs) for i in self.children).strip()
		ident = re.sub(r'<[^>]*>', '', ident, flags=globalv.re_flags)
		ident = re.sub(r'\s', '-', ident, flags=globalv.re_flags)
		ident = html.escape(ident)

		# Make sure it's unique on the whole document
		while ident in globalv.html_document_ids:
			ident += '_'
		globalv.html_document_ids.add(ident)

		return '<h%d id="%s">' % (self.level, ident)\
		       + '<br>'.join(i.emit_html(**kwargs) for i in self.children) + "</h%d>" % self.level

	def emit_rtf(self, **kwargs):
		# TODO: Distinguish between levels of headings
		styles = {
			# level: style index
			1: 2,
			2: 3,
			3: 4,
			4: 4,
			5: 4,
			6: 4
		}
		return (r'{\pard\sa180\sb90\keepn\s%d ' % styles[self.level]) + \
		       r'\line '.join(i.emit_rtf(**kwargs) for i in self.children) + r'\par}'

	def emit_latex(self, **kwargs):
		levels = {
			1: r'\section{',
			2: r'\subsection{',
			3: r'\subsubsection{',
		}
		return levels.get(self.level, r'\subsubsection{') + r'\\'.join(i.emit_latex(**kwargs) for i in self.children) + '}\n'

	def emit_jd(self, **kwargs):
		# TODO: Emit the other style of heading canonically?
		return '\n\n' + '#' * self.level + ' ' + ''.join(i.emit_jd(**kwargs) for i in self.children) + '\n\n'


class HorizontalRule(Node):
	def emit_html(self, **kwargs):
		return "<hr/>"

	def emit_latex(self, **kwargs):
		return '\n' + r'\rule{\textwidth}{1pt}' + '\n'

	def emit_jd(self, **kwargs):
		return '\n\n---\n\n'


class List(Node):
	pass


class UList(List):
	def emit_html(self, **kwargs):
		res = "<ul>"
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += "</ul>"
		return res

	def emit_latex(self, **kwargs):
		res = r'\begin{itemize}' + '\n'
		for item in self.children:
			res += item.emit_latex(**kwargs)
		res += '\n' + r'\end{itemize}' + '\n'
		return res

	def emit_jd(self, **kwargs):
		res = []
		for item in self.children:
			if isinstance(item, List):
				res.extend('\t' + i for i in item.emit_jd(**kwargs).split('\n'))
			else:
				res.append()


class OList(List):
	def __init__(self, children=None, list_type='1', start=1):
		super().__init__(children)
		self.start = start
		self.list_type = list_type

	def emit_html(self, **kwargs):
		res = '<ol start="%s" type="%s">' % (self.start, self.list_type)
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += "</ol>"
		return res

	def emit_latex(self, **kwargs):
		res = r'\begin{enumerate}' + '\n'
		for item in self.children:
			res += item.emit_latex(**kwargs)
		res += '\n' + r'\end{enumerate}' + '\n'
		return res


class CheckList(UList):
	def emit_html(self, **kwargs):
		res = '<ul class="checklist">'
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += '</ul>'
		return res


class ReferenceList(OList):
	def __init__(self):
		items = [ReferenceItem(ref_key, content[0]) for ref_key, content in globalv.references.items()]
		super().__init__(items, '1')

	def emit_html(self, **kwargs):
		res = '<ol class="references" start="%s">' % self.start
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += '</ol>'
		return res

	def emit_latex(self, **kwargs):
		res = r' \begin{thebibliography}{%s}' % len(globalv.references) + '\n'
		res += '\n'.join(i.emit_latex(**kwargs) for i in self.children)
		res += r' \end{thebibliography}'
		return res


class ListItem(Node):
	def emit_html(self, **kwargs):
		res = ["<li><span>", ''.join(i.emit_html(**kwargs) for i in self.children[:-1])]

		if self.children and isinstance(self.children[-1], List):
			res.append("</span>" + self.children[-1].emit_html(**kwargs))
		elif self.children:
			res.append(self.children[-1].emit_html(**kwargs) + "</span>")

		return ''.join(res)

	def emit_latex(self, **kwargs):
		return r'\item ' + ''.join(i.emit_latex(**kwargs) for i in self.children) + '\n'


class ChecklistItem(Node):
	def __init__(self, checked, children):
		self.checked = checked
		super().__init__(children)

	def emit_html(self, **kwargs):
		css_class = 'checked' if self.checked else 'unchecked'
		res = ['<li class="%s"><span>' % css_class, ''.join(i.emit_html(**kwargs) for i in self.children[:-1])]

		if self.children and isinstance(self.children[-1], List):
			res.append("</span>" + self.children[-1].emit_html(**kwargs))
		elif self.children:
			res.append(self.children[-1].emit_html(**kwargs) + "</span>")

		return ''.join(res)



class ReferenceItem(Node):
	def __init__(self, ref_key, content):
		self.ref_key = ref_key
		self.content = content
		super().__init__()

	def emit_html(self, **kwargs):
		return '<li><a id="%s"><span>%s</span></a></li>' % (self.ref_key, self.content.emit_html(**kwargs))

	def emit_latex(self, **kwargs):
		return r'\bibitem{%s} %s ' % (self.ref_key, self.content.emit_latex(**kwargs))


class Paragraph(Node):
	def emit_html(self, **kwargs):
		return "<p>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</p>"

	def emit_rtf(self, **kwargs):
		return r'{\pard\s1 ' + r'\line '.join(i.emit_rtf(**kwargs) for i in self.children) + r'\par}'

	def emit_latex(self, **kwargs):
		return r'\par ' + r'\\ '.join(i.emit_latex(**kwargs) for i in self.children)


class CodeBlock(Node):
	def emit_html(self, **kwargs):
		return "<code class=\"console\">" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</code>"

	def emit_rtf(self, **kwargs):
		return r'''
{\pard\sa180\li720\ri720\keep\f2
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
''' + r'\line '.join(i.emit_rtf(**kwargs) for i in self.children) + r'\par}'

	def emit_latex(self, **kwargs):
		return r'\begin{lstlisting}' + '\n' + \
		       ''.join(i.emit_latex(**kwargs) for i in self.children) + \
		       r'\end{lstlisting}' + '\n'


class MathBlock(Node):
	def emit_html(self, **kwargs):
		return "<div class='math'>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</div>"

	def emit_rtf(self, **kwargs):
		return r'''
{\pard\sa180\li720\ri720\keep
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
''' + r'\line '.join(i.emit_rtf(**kwargs) for i in self.children) + r'\par}'

	def emit_latex(self, **kwargs):
		return r'\begin{gather*}' + '\n' + '\n'.join(i.emit_latex(**kwargs) for i in self.children) + '\n' + r'\end{gather*}'


class Blockquote(Node):
	def emit_html(self, **kwargs):
		return "<blockquote>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</blockquote>"

	def emit_rtf(self, **kwargs):
		return r'''
{\pard\sa180\li720\ri720\keep\f1
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
''' + r'\line '.join(i.emit_rtf(**kwargs) for i in self.children) + r'\par}'

	def emit_latex(self, **kwargs):
		return r'\begin{displayquote}' + '\n' +\
	r'\\'.join(i.emit_latex(**kwargs) for i in self.children) + r'\end{displayquote}' + '\n'


class Math(Node):
	def emit_html(self, **kwargs):
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs):
		text = ''.join(i.emit_latex(**kwargs) for i in self.children)
		for regex, subst in latex_math_subst:
			text = text.replace(regex, subst)
		return text


class Table(Node):
	def __init__(self, caption, alignment, children=None):
		super().__init__(children)
		self.caption = caption
		self.alignment = alignment

	def emit_html(self, **kwargs):
		caption_html = ''
		if self.caption:
			caption_html = '<caption>' + ''.join(i.emit_html(**kwargs) for i in self.caption) + '</caption>'
		return '<table>' + caption_html + \
			'<thead>' + self.children[0].emit_html(**kwargs) + '</thead>' +\
		    '<tbody>' + ''.join(i.emit_html(**kwargs) for i in self.children[1:]) + '</tbody></table>'

	def emit_latex(self, **kwargs):
		caption_latex = ''
		if self.caption:
			caption_latex = r'\caption{' + ''.join(i.emit_latex(**kwargs) for i in self.caption) + '}'
		alignment_map = {
			0: 'l',
			1: 'c',
			2: 'r',
		}
		alignment_string = '{' + '|'.join(alignment_map[i] for i in self.alignment) + '}'
		res = r'\begin{table}' + '\n' + caption_latex + '\n'
		res += r'\begin{tabular}' + alignment_string + '\n'
		res += self.children[0].emit_latex(**kwargs) + r'\\ \hline '
		res += ' \\\\\n'.join(i.emit_latex(**kwargs) for i in self.children[1:])
		res += r'\end{tabular}' + '\n' + '\end{table}'
		return res


class TableRow(Node):
	def emit_html(self, **kwargs):
		return "<tr>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</tr>"

	def emit_latex(self, **kwargs):
		return ' & '.join(i.emit_latex(**kwargs) for i in self.children)


class TableHeader(Node):
	def emit_html(self, **kwargs):
		return "<th>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</th>"

	def emit_latex(self, **kwargs):
		return ''.join(i.emit_latex(**kwargs) for i in self.children)


class TableCell(Node):
	align_map = {
		0: 'left',
		1: 'center',
		2: 'right'
	}

	def __init__(self, align, children=None):
		super().__init__(children=children)
		self.align = align

	def emit_html(self, **kwargs):
		return '<td style="text-align: %s;">' % self.align_map[self.align] +\
		       ''.join(i.emit_html(**kwargs) for i in self.children) + '</td>'

	def emit_latex(self, **kwargs):
		return ''.join(i.emit_latex(**kwargs) for i in self.children)


class Link(Node):
	def __init__(self, linked_text, url):
		# TODO: make this take a generic list of children instead of linked_text node
		super().__init__([linked_text])
		self.url = html.escape(url)
		self.linked_text = linked_text

	def emit_html(self, link_translation=None, **kwargs):
		url = self.url
		if link_translation:
			url = globalv.ext_translation(url, link_translation)

		return '<a href="' + url + '">' + self.linked_text.emit_html(link_translation=link_translation, **kwargs) + '</a>'

	def emit_rtf(self, link_translation=None, **kwargs):
		url = self.url
		if link_translation:
			url = globalv.ext_translation(url, link_translation)

		linked_cited = self.linked_text.emit_html(
			link_translation=link_translation,
			**kwargs
		)

		return r'''{\field{\*\fldinst{HYPERLINK "%s"
}}{\fldrslt{\ul
%s
}}}''' % (url, linked_cited)

	def emit_latex(self, link_translation=None, **kwargs):
		url = self.url
		if link_translation:
			url = globalv.ext_translation(url, link_translation)
		return r' \href{%s}{%s} ' % (
			url,
			self.linked_text.emit_latex(link_translation=link_translation, **kwargs)
		)


class ReferenceLink(Node):
	def __init__(self, cited_node, ref_key):
		# TODO:  make this take a generic list of children instead of a singleton cited_node
		super().__init__([cited_node])
		self.cited_node = cited_node
		self.ref_key = ref_key

	def emit_html(self, link_translation=None, ref_style=False, **kwargs):
		if not globalv.references[self.ref_key]:
			raise Exception("Missing definition for reference '%s'" % self.ref_key)
		if ref_style:
			place = list(globalv.references.keys()).index(self.ref_key) + 1
			emitted_html = self.cited_node.emit_html(
				link_translation=link_translation,
				ref_style=True,
				**kwargs
			)
			return '%s<cite>[<a href="#%s" class="reference">%d</a>]</cite>' % (emitted_html, self.ref_key, place)
		else:
			_, href = globalv.references[self.ref_key]
			href = html.escape(href)
			if link_translation:
				href = link_translation(href, link_translation)
			return '<a href="%s">%s</a>' % (href, self.cited_node)

	def emit_rtf(self, link_translation=None, ref_style=False, **kwargs):
		if not globalv.references[self.ref_key]:
			raise Exception("Missing definition for reference '%s'" % self.ref_key)

		cited_emmited = self.cited_node.emit_rtf(
			link_translation=link_translation,
			ref_style=ref_style,
			**kwargs
		)
		if ref_style:
			ref_emmited, _ = globalv.references[self.ref_key].emit_rtf(
				link_translation,
				ref_style,
				**kwargs
			)
			return r'%s{\super\chftn}{\footnote\pard\plain\chftn %s}' % (cited_emmited, ref_emmited)
		else:
			_, href = globalv.references[self.ref_key]
			href = html.escape(href)
			if link_translation:
				href = link_translation(href, link_translation)
			return r'''{\field{\*\fldinst{HYPERLINK
"%s"
}}{\fldrslt{\ul
%s
}}}''' % (href, cited_emmited)

	def emit_latex(self, link_translation=None, ref_style=False, **kwargs):
		if not globalv.references[self.ref_key]:
			raise Exception("Missing definition for reference '%s'" % self.ref_key)
		if ref_style:
			ref_emmited = self.cited_node.emit_latex(
				link_translation=link_translation,
				ref_style=True,
				**kwargs
			)
			return r'%s \cite{%s}' % (ref_emmited, self.ref_key)
		else:
			_, href = globalv.references[self.ref_key]
			href = html.escape(href)
			if link_translation:
				href = link_translation(href, link_translation)
			return r' \href{%s}{%s}' % (href, self.cited_node)


class Content(Node):
	def __init__(self, alt, src, title, children=None):
		super().__init__(children)
		self.alt = alt
		self.src = src
		self.title = title if title else TextNode('')

	def emit_html(self, **kwargs):
		# TODO: Allow embedding of data to eliminate the need to link to it (maybe even downloading stuff from the web
		dtype = globalv.content_filetypes(self.src)
		if dtype == 'image':
			elem = '<img src="%s" title="%s" alt="%s">' % (self.src, self.title.emit_html(**kwargs), self.alt.emit_html(**kwargs))
		elif dtype == 'audio':
			elem = '<audio src="%s" controls>%s</audio>' % (self.src, self.alt.emit_html(**kwargs))
		elif dtype == 'video':
			elem = '<video src="%s" controls>%s</video>' % (self.src, self.alt.emit_html(**kwargs))
		elif dtype == 'flash':
			elem = '<object data="%s" type="application/x-shockwave-flash"></object>' % self.src
		else:
			elem = '<object data="%s"></object>' % self.src

		# TODO: make figures a command line option
		return '<figure>%s<figcaption>%s</figcaption></figure>' % (elem, self.title.emit_html(**kwargs))

	def emit_latex(self, **kwargs):
		dtype = globalv.content_filetypes(self.src)
		if dtype == 'image':
			elem = r'\includegraphics[width=\textwidth]{%s}' % self.src
		else:
			elem = ''

		return r'''
\begin{figure}
\begin{center}
\caption{%s}
%s
\end{center}
\end{figure}
''' % (self.title, elem)


class ImplicitLink(TextNode):
	def emit_html(self, **kwargs):
		return '<a href="' + self.text + '" class="implicit">' + self.text + '</a>'

	def emit_rtf(self, **kwargs):
		return r'''{\field{\*\fldinst{HYPERLINK "%s"
}}{\fldrslt{\ul
%s
}}}''' % (self.text, self.text)

	def emit_latex(self, **kwargs):
		return r' \url{%s}' % self.text


class ImplicitEmail(TextNode):
	def emit_html(self, **kwargs):
		return '<a href="mailto:' + self.text + '" class="implicit">' + self.text + '</a>'

	def emit_rtf(self, **kwargs):
		return r'''{\field{\*\fldinst{HYPERLINK "mailto:%s"
}}{\fldrslt{\ul
%s
}}}''' % (self.text, self.text)

	def emit_latex(self, **kwargs):
		return r'\href{mailto:%s}{%s}' % (self.text, self.text)


# For text ----------------------------------------------------------------------

class Plaintext(TextNode):
	pass

# TODO: Shouldn't this be a text node?
class CodeInline(Node):
	def emit_html(self, **kwargs):
		return "<code>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</code>"

	def emit_latex(self, **kwargs):
		return r'\texttt{' + ''.join(i.emit_html(**kwargs) for i in self.children) + '}'


class Emph(Node):
	def emit_html(self, **kwargs):
		return "<em>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</em>"

	def emit_rtf(self, **kwargs):
		return r'{\i ' + ''.join(i.emit_rtf(**kwargs) for i in self.children) + '}'

	def emit_latex(self, **kwargs):
		return r'\textit{' + ''.join(i.emit_latex(**kwargs) for i in self.children) + '}'


class Strong(Node):
	def emit_html(self, **kwargs):
		return "<strong>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</strong>"

	def emit_rtf(self, **kwargs):
		return r'{\b ' + ''.join(i.emit_rtf(**kwargs) for i in self.children) + '}'

	def emit_latex(self, **kwargs):
		return r'\textbf{' + ''.join(i.emit_latex(**kwargs) for i in self.children) + '}'


class StrongEmph(Node):
	def emit_html(self, **kwargs):
		return "<strong><em>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</em></strong>"

	def emit_rtf(self, **kwargs):
		return r'{\b \i ' + ''.join(i.emit_rtf(**kwargs) for i in self.children) + '}'

	def emit_latex(self, **kwargs):
		return r'\textit{\textbf{' + ''.join(i.emit_latex(**kwargs) for i in self.children) + '}}'


class Strikethrough(Node):
	def emit_html(self, **kwargs):
		return "<del>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</del>"

	def emit_rtf(self, **kwargs):
		return r'{\strike ' + r'\line '.join(i.emit_rtf(**kwargs) for i in self.children) + r'\par}'


# MATH -------------------

class MathInline(Node):
	def emit_html(self, **kwargs):
		return '<span class="math">' + ''.join(i.emit_html(**kwargs) for i in self.children) + '</span>'

	def emit_latex(self, **kwargs):
		text = ''.join(i.emit_latex(**kwargs) for i in self.children)
		for regex, subst in latex_math_subst:
			text = text.replace(regex, subst)
		return '$' + text + '$'


class Parenthesis(Node):
	def emit_html(self, **kwargs):
		return "(" + ''.join(i.emit_html(**kwargs) for i in self.children) + ")"

	def emit_mathml(self, **kwargs):
		return "<mfenced open=\"(\" close=\")\"><mrow>" + ''.join(i.emit_mathml(**kwargs) for i in self.children)\
		       + "</mrow></mfenced>"

	def emit_latex(self, **kwargs):
		return '(' + ''.join(i.emit_latex(**kwargs) for i in self.children) + ')'


class Braces(Node):
	def emit_html(self, **kwargs):
		return "{ " + ''.join(i.emit_html(**kwargs) for i in self.children) + " }"

	def emit_latex(self, **kwargs):
		return r'\{' + ''.join(i.emit_latex(**kwargs) for i in self.children) + r'\}'


class Brackets(Node):
	def emit_html(self, **kwargs):
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs):
		return ''.join(i.emit_mathml(**kwargs) for i in self.children)


class Sum(Node):
	def emit_html(self, **kwargs):
		# return "∑"
		return """
	<math><mstyle displaystyle="true"><mrow>
	<munderover>
		<mo>&sum;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></mstyle></math>
	""" % (self.children[0].emit_mathml(**kwargs),
		   self.children[1].emit_mathml(**kwargs)) + ''.join(i.emit_html(**kwargs) for i in self.children[2:])

	def emit_latex(self, **kwargs):
		return r'\displaystyle\sum^{%s}_{%s} %s' % (
			self.children[1].emit_latex(**kwargs),
			self.children[0].emit_latex(**kwargs),
			''.join(i.emit_latex(**kwargs) for i in self.children[2:])
		)


class Prod(Node):
	def emit_html(self, **kwargs):
		# return "∏"
		return """
	<math><mstyle displaystyle="true"><mrow>
	<munderover>
		<mo>&prod;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></mstyle></math>
	""" % (self.children[0].emit_mathml(**kwargs),
		   self.children[1].emit_mathml(**kwargs)) + ''.join(i.emit_html(**kwargs) for i in self.children[2:])

	def emit_latex(self, **kwargs):
		return r'\displaystyle\prod^{%s}_{%s} %s' % (
			self.children[1].emit_latex(**kwargs),
			self.children[0].emit_latex(**kwargs),
			''.join(i.emit_latex(**kwargs) for i in self.children[2:])
		)


class Int(Node):
	def emit_html(self, **kwargs):
		# return "∏"
		return """
	<math><mstyle displaystyle="true"><mrow>
	<munderover>
		<mo>&int;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></mstyle></math>
	""" % (self.children[0].emit_mathml(**kwargs),
		   self.children[1].emit_mathml(**kwargs)) + ''.join(i.emit_html(**kwargs) for i in self.children[2:])

	def emit_latex(self, **kwargs):
		return r'\displaystyle\sum^{%s}_{%s} %s' % (
			self.children[1].emit_latex(**kwargs),
			self.children[0].emit_latex(**kwargs),
			''.join(i.emit_latex(**kwargs) for i in self.children[2:])
		)

#TODO: Properly nest Subscript and Superscript nodes, having both the base and "exponent"

class SuperscriptBrackets(Node):
	def emit_html(self, **kwargs):
		return "<sup>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</sup>"

	def emit_mathml(self, **kwargs):
		return "<msup><msrow></msrow><msrow>" + ''.join(i.emit_mathml(**kwargs) for i in self.children) + "</msrow></mssup>"

	def emit_latex(self, **kwargs):
		return '^{' + ''.join(i.emit_latex(**kwargs) for i in self.children) + '}'


class SubscriptBrackets(Node):
	def emit_html(self, **kwargs):
		return "<sub>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</sub>"

	def emit_mathml(self, **kwargs):
		return "<msub><msrow></msrow><msrow>" + ''.join(i.emit_mathml(**kwargs) for i in self.children) + "</msrow></mssub>"

	def emit_latex(self, **kwargs):
		return '_{' + ''.join(i.emit_latex(**kwargs) for i in self.children) + '}'


class Subscript(TextNode):
	def emit_html(self, **kwargs):
		return "<sub>" + html.escape(self.text, quote=True) + "</sub>"

	def emit_mathml(self, **kwargs):
		return "<msub><mrow></mrow><mrow>" + html.escape(self.text, quote=True) + "</mrow></mssub>"

	def emit_latex(self, **kwargs):
		return '_{' + self.text + '}'


class Superscript(TextNode):
	def emit_html(self, **kwargs):
		return "<sup>" + html.escape(self.text, quote=True) + "</sup>"

	def emit_mathml(self, **kwargs):
		return "<msup><mrow></mrow><mrow>" + html.escape(self.text, quote=True) + "</mrow></mssup>"

	def emit_latex(self, **kwargs):
		return '^{' + self.text + '}'


class Identifier(TextNode):
	def emit_html(self, **kwargs):
		return "<em>" + html.escape(self.text, quote=True) + "</em>"

	def emit_mathml(self, **kwargs):
		return "<mi>" + self.text + "</mi>"


class Operator(TextNode):
	def emit_html(self, **kwargs):
		return " %s " % html.escape(self.text, quote=True)

	def emit_mathml(self, **kwargs):
		return "<mo>" + self.text + "</mo>"


class Comment(TextNode):
	def emit_html(self, **kwargs):
		return ' %s ' % html.escape(self.text, quote=True)

	def emit_latex(self, **kwargs):
		return r' \text{' + self.text + '} '


class Number(TextNode):
	def emit_mathml(self, **kwargs):
		return "<mn>" + self.text + "</mn>"


class Newline(TextNode):
	def emit_html(self, **kwargs):
		return "<br>"

	def emit_latex(self, **kwargs):
		return r'\\'
