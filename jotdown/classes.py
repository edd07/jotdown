# -*- coding: utf-8 -*-
import html
import os
import re
from getpass import getuser
from socket import gethostname
from typing import Sequence, Iterable

import jotdown.globalv as globalv
from jotdown.regex import latex_math_subst


# Abstract ---------------------------------
class Node:
	def __init__(self, children: Iterable['Node']=None) -> None:
		self.children = children if children else []

	def emit_html(self, **kwargs) -> str:
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return ''.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_debug(self, indent: int=0, **kwargs) -> str:
		return ('\t' * indent) + type(self).__name__ + '\n' + ''.join(i.emit_debug(indent + 1, **kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return ''.join(i.emit_jd(**kwargs) for i in self.children)


class TextNode(Node):
	def __init__(self, text: str) -> None:
		super().__init__()
		self.text = text

	def emit_html(self, **kwargs) -> str:
		return html.escape(self.text, quote=True)

	def emit_rtf(self, **kwargs) -> str:
		return globalv.rtf_escape_unicode(self.text)

	def emit_latex(self, **kwargs) -> str:
		special_chars = (
			# LATEX needs these characters escaped in source files
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
			('—', r'---'),  # em dash
			('–', r'--'),   # en dash
			('>', r'\textgreater '),
			('<', r'\textless '),
		)
		text = self.text
		for old, new in special_chars:
			text = text.replace(old, new)
		return text

	def emit_debug(self, indent: int=0, **kwargs) -> str:
		summary = repr(self.text[:50])
		if len(self.text) > len(summary):
			summary += '...'
		res = ('\t' * indent) + type(self).__name__ + ' ' + summary + '\n'
		res += ''.join(i.emit_debug(indent + 1, **kwargs) for i in self.children)
		return res

	def emit_jd(self, **kwargs) -> str:
		return self.text


# For blocks -------------------------------------------------------------------------


class Document(Node):
	def __init__(self, children: Sequence[Node]=None, name: str="Jotdown Document", author: str=None) -> None:
		super().__init__(children)
		self.name = name
		self.author = getuser() if not author else author
		self.hostname = gethostname()

	def emit_html(self, stylesheet: str, stylesheet_enc: str=None, ref_style: bool=False, embed_css: bool=True, **kwargs) -> str:
		if embed_css:
			css_string = '<style>%s</style>' % globalv.read_with_encoding(stylesheet, stylesheet_enc)
		else:
			css_string = '<link rel="stylesheet" href="%s"/>' % stylesheet

		footer = '<footer>%s</footer>' % ReferenceList().emit_html(ref_style=True, **kwargs) if ref_style else ''
		# TODO: Author and creation time meta tags
		return '''<!DOCTYPE html><html>
<head>
<title>%s</title>
<meta charset="UTF-8">%s
</head>
<body>
%s
%s
</body>
</html>
''' % (
			self.name,
			css_string,
			'\n'.join(block.emit_html(ref_style=ref_style, **kwargs) for block in self.children),
			footer,
		)

	def emit_rtf(self, stylesheet: str, stylesheet_enc: str=None, **kwargs) -> str:
		tables = globalv.read_with_encoding(stylesheet, stylesheet_enc)
		# TODO: Author in info, and create time
		return r'''{\rtf1\ansi\deff0\widowctrl %s
{\info
{\title %s}
{\author PLACEHOLDER}
{\creatim\yr2016\mo7\dy20\hr18\min37}
}
''' % (tables, self.name) + ''.join(block.emit_rtf(**kwargs) for block in self.children) + '}'

	def emit_latex(self, stylesheet: str, stylesheet_enc: str=None, ref_style: bool=False, **kwargs) -> str:
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
		return globalv.read_with_encoding(stylesheet, stylesheet_enc) % field_dict


class Heading(Node):
	def __init__(self, level: int, children: Sequence[Node]=None) -> None:
		super().__init__(children)
		self.level = min(level, 6)

	def emit_html(self, **kwargs) -> str:
		# Sanitize the text for the id
		ident = ''.join(i.emit_html(**kwargs) for i in self.children).strip()
		ident = re.sub(r'<[^>]*>', '', ident, flags=globalv.re_flags)
		ident = re.sub(r'\s', '-', ident, flags=globalv.re_flags)
		ident = html.escape(ident)

		# Make sure it's unique on the whole document
		while ident in globalv.html_document_ids:
			ident += '_'
		globalv.html_document_ids.add(ident)

		return '<h%d id="%s">%s</h%d>' % (
			self.level,
			ident,
			'<br>'.join(i.emit_html(**kwargs) for i in self.children),
			self.level,
		)

	def emit_rtf(self, **kwargs) -> str:
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

	def emit_latex(self, **kwargs) -> str:
		levels = {
			1: r'\section{',
			2: r'\subsection{',
			3: r'\subsubsection{',
		}
		return levels.get(self.level, r'\subsubsection{') + r'\\'.join(i.emit_latex(**kwargs) for i in self.children) + '}\n'

	def emit_jd(self, **kwargs) -> str:
		# TODO: Emit the other style of heading canonically?
		return '%s %s\n\n' % (
			'#' * self.level,
			''.join(i.emit_jd(**kwargs) for i in self.children),
		)


class HorizontalRule(Node):
	def emit_html(self, **kwargs) -> str:
		return '<hr/>'

	def emit_latex(self, **kwargs) -> str:
		return '\n%s\n' % r'\rule{\textwidth}{1pt}'

	def emit_jd(self, **kwargs) -> str:
		return '---\n\n'


class ListNode(Node):
	pass


class UList(ListNode):
	def emit_html(self, **kwargs) -> str:
		return '<ul>%s</ul>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'''\begin{itemize}
%s
\end{itemize}
''' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, depth: int=0, **kwargs) -> str:
		list_res = []
		for list_item in self.children:
			list_item_res = []
			for node in list_item.children:
					list_item_res.append(node.emit_jd(depth=depth + 1, **kwargs))
			list_res.append('\t' * depth + '* ' +''.join(list_item_res))
		return '\n'.join(list_res) + ('\n' if depth == 0 else '')


class OList(ListNode):
	def __init__(self, children: Sequence[Node]=None, list_type: str='1', start: int=1) -> None:
		super().__init__(children)
		self.start = start
		self.list_type = list_type

	def emit_html(self, **kwargs) -> str:
		return '<ol start="%s" type="%s">%s</ol>' % (
			self.start,
			self.list_type,
			''.join(i.emit_html(**kwargs) for i in self.children),
		)

	def emit_latex(self, **kwargs) -> str:
		return r'''\begin{enumerate}
%s
\end{enumerate}
''' % (''.join(i.emit_latex(**kwargs) for i in self.children))

	def emit_jd(self, depth: int=0, **kwargs) -> str:
		list_res = []
		for n, list_item in enumerate(self.children):
			list_item_res = []
			for node in list_item.children:
				list_item_res.append(node.emit_jd(depth=depth + 1, **kwargs))
			# TODO: Support the other list types
			list_res.append('\t' * depth + str(n + 1) + ' ' +''.join(list_item_res))
		return '\n'.join(list_res) + ('\n' if depth == 0 else '')


class CheckList(UList):
	def emit_html(self, **kwargs) -> str:
		return '<ul class="checklist">%s</ul>' % ''.join(i.emit_html(**kwargs) for i in self.children)


class ReferenceList(OList):
	def __init__(self) -> None:
		items = [ReferenceItem(ref_key, content[0]) for ref_key, content in globalv.references.items()]
		super().__init__(items, '1')

	def emit_html(self, **kwargs) -> str:
		return '<ol class="references" start="%s">%s</ol>' % (
			self.start,
			''.join(i.emit_html(**kwargs) for i in self.children),
		)

	def emit_latex(self, **kwargs) -> str:
		return r'''\begin{thebibliography}{%s}
%s
\end{thebibliography}
''' % (
			len(globalv.references),
			'\n'.join(i.emit_latex(**kwargs) for i in self.children),
		)


class ListItem(Node):
	def emit_html(self, **kwargs) -> str:
		res = ["<li><span>", ''.join(i.emit_html(**kwargs) for i in self.children[:-1])]

		if self.children and isinstance(self.children[-1], ListNode):
			res.append("</span>" + self.children[-1].emit_html(**kwargs))
		elif self.children:
			res.append(self.children[-1].emit_html(**kwargs) + "</span>")

		return ''.join(res)

	def emit_latex(self, **kwargs) -> str:
		return r'\item %s\n' % ''.join(i.emit_latex(**kwargs) for i in self.children)


class ChecklistItem(Node):
	def __init__(self, checked: bool, children: Sequence[Node]=None):
		self.checked = checked
		super().__init__(children)

	def emit_html(self, **kwargs) -> str:
		css_class = 'checked' if self.checked else 'unchecked'
		res = ['<li class="%s"><span>' % css_class, ''.join(i.emit_html(**kwargs) for i in self.children[:-1])]

		if self.children and isinstance(self.children[-1], ListNode):
			res.append("</span>" + self.children[-1].emit_html(**kwargs))
		elif self.children:
			res.append(self.children[-1].emit_html(**kwargs) + "</span>")

		return ''.join(res)


class ReferenceItem(Node):
	def __init__(self, ref_key, content) -> None:
		self.ref_key = ref_key
		self.content = content
		super().__init__()

	def emit_html(self, **kwargs) -> str:
		return '<li><a id="%s"><span>%s</span></a></li>' % (self.ref_key, self.content.emit_html(**kwargs))

	def emit_latex(self, **kwargs) -> str:
		return r'\bibitem{%s} %s ' % (self.ref_key, self.content.emit_latex(**kwargs))


class Paragraph(Node):
	def emit_html(self, **kwargs) -> str:
		return '<p>%s</p>' % '<br>'.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'{\pard\s1 %s\par}' % r'\line '.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\par %s' % r'\\ '.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return ''.join(i.emit_jd(**kwargs) for i in self.children) + '\n'


class CodeBlock(Node):
	def emit_html(self, **kwargs) -> str:
		return '<code class="console">%s</code>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'''
{\pard\sa180\li720\ri720\keep\f2
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
%s
\par}
''' % r'\line '.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'''\begin{lstlisting}
%s
\end{lstlisting}
''' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '```\n%s\n```' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class MathBlock(Node):
	def emit_html(self, **kwargs) -> str:
		return "<div class='math'>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</div>"

	def emit_rtf(self, **kwargs) -> str:
		return r'''
{\pard\sa180\li720\ri720\keep
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
%s
\par}
''' % r'\line '.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'''\begin{gather*}
%s
\end{gather*}
''' % '\n'.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '«««\n%s\n»»»' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Blockquote(Node):
	def emit_html(self, **kwargs) -> str:
		return '<blockquote>%s</blockquote>' % '<br>'.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'''
{\pard\sa180\li720\ri720\keep\f1
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
%s
\par}
''' % r'\line '.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'''\begin{displayquote}
%s
\end{displayquote}
''' % r'\\'.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return ''.join('>' + i.emit_jd(**kwargs) for i in self.children) + '\n'


class Math(Node):
	def emit_html(self, **kwargs) -> str:
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		text = ''.join(i.emit_latex(**kwargs) for i in self.children)
		for regex, subst in latex_math_subst:
			text = text.replace(regex, subst)
		return text


class Table(Node):
	latex_alignment_map = {
		0: 'l',
		1: 'c',
		2: 'r',
	}

	def __init__(self, caption: Sequence[Node], alignment: Sequence[int], children: Sequence[Node]=None) -> None:
		super().__init__(children)
		self.caption = caption
		self.alignment = alignment

	def emit_html(self, **kwargs) -> str:
		caption_html = '<caption>%s</caption>' % ''.join(i.emit_html(**kwargs) for i in self.caption) if self.caption else ''
		return '''<table>
%s
<thead>%s</thead>
<tbody>%s</tbody>
</table>
''' % (
			caption_html,
			self.children[0].emit_html(**kwargs),
			''.join(i.emit_html(**kwargs) for i in self.children[1:]),
		)

	def emit_latex(self, **kwargs) -> str:
		caption_latex = r'\caption{%s}' % ''.join(i.emit_latex(**kwargs) for i in self.caption) if self.caption else ''
		alignment_string = '{%s}' % '|'.join(self.alignment_map[i] for i in self.alignment)

		return r'''\begin{table}
%s
\begin{tabular}%s
%s\\ \hline
%s
\end{tabular}
\end{table}
''' % (
			caption_latex,
			alignment_string,
			self.children[0].emit_latex(**kwargs),
			' \\\\\n'.join(i.emit_latex(**kwargs) for i in self.children[1:])
		)

	def emit_jd(self, **kwargs) -> str:
		return '«%s»' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class TableRow(Node):
	def emit_html(self, **kwargs) -> str:
		return '<tr>%s</tr>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return ' & '.join(i.emit_latex(**kwargs) for i in self.children)


class TableHeader(Node):
	def emit_html(self, **kwargs) -> str:
		return '<th>%s</th>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return ''.join(i.emit_latex(**kwargs) for i in self.children)


class TableCell(Node):
	html_align_map = {
		0: 'left',
		1: 'center',
		2: 'right'
	}

	def __init__(self, align: int, children: Sequence[Node]=None) -> None:
		super().__init__(children=children)
		self.align = align

	def emit_html(self, **kwargs) -> str:
		return '<td style="text-align: %s;">%s</td>' % (
			self.html_align_map[self.align],
			''.join(i.emit_html(**kwargs) for i in self.children),
		)

	def emit_latex(self, **kwargs) -> str:
		return ''.join(i.emit_latex(**kwargs) for i in self.children)


class Link(Node):
	def __init__(self, linked_text: Node, url: str) -> Node:
		# TODO: make this take a generic list of children instead of linked_text node
		super().__init__([linked_text])
		self.url = html.escape(url)
		self.linked_text = linked_text

	def emit_html(self, link_translation: str=None, **kwargs) -> str:
		url = self.url
		if link_translation:
			url = globalv.ext_translation(url, link_translation)

		return '<a href="%s">%s</a>' % (
			url,
			self.linked_text.emit_html(link_translation=link_translation, **kwargs),
		)

	def emit_rtf(self, link_translation: str=None, **kwargs) -> str:
		url = globalv.ext_translation(self.url, link_translation) if link_translation else self.url

		linked_cited = self.linked_text.emit_html(
			link_translation=link_translation,
			**kwargs
		)

		return r'''{\field{\*\fldinst{HYPERLINK "%s"
}}{\fldrslt{\ul
%s
}}}''' % (url, linked_cited)

	def emit_latex(self, link_translation: str=None, **kwargs) -> str:
		url = self.url
		if link_translation:
			url = globalv.ext_translation(url, link_translation)
		return r' \href{%s}{%s} ' % (
			url,
			self.linked_text.emit_latex(link_translation=link_translation, **kwargs)
		)

	def emit_jd(self, **kwargs) -> str:
		# No extension translation needed when exporting to .jd
		return '[%s](%s)' % (self.linked_text.emit_jd(**kwargs), self.url)


class ReferenceLink(Node):
	def __init__(self, cited_node: Node, ref_key: str) -> None:
		# TODO:  make this take a generic list of children instead of a singleton cited_node
		super().__init__([cited_node])
		self.cited_node = cited_node
		self.ref_key = ref_key

	def emit_html(self, link_translation: str=None, ref_style: bool=False, **kwargs) -> str:
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

	def emit_rtf(self, link_translation: str=None, ref_style: bool=False, **kwargs) -> str:
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

	def emit_latex(self, link_translation: str=None, ref_style: bool=False, **kwargs) -> str:
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
				href = globalv.ext_translation(href, link_translation)
			return r' \href{%s}{%s}' % (href, self.cited_node)


class Content(Node):
	def __init__(self, alt: Node, src: str, title: Node, children: Sequence[Node]=None) -> None:
		super().__init__(children)
		self.alt = alt
		self.src = src
		self.title = title if title else TextNode('')

	def emit_html(self, **kwargs) -> str:
		# TODO: Allow embedding of data to eliminate the need to link to it (maybe even downloading stuff from the web
		dtype = globalv.content_filetypes(self.src)
		attributes = {
			'src': self.src,
			'title': self.title.emit_html(**kwargs),
			'alt': self.alt.emit_html(**kwargs),
		}
		if dtype == 'image':
			template = '<img src="%(src)s" title="%(title)s" alt="%(alt)s">'
		elif dtype == 'audio':
			template = '<audio src="%(src)s" controls>%(alt)s</audio>'
		elif dtype == 'video':
			template = '<video src="%(src)s" controls>%(alt)s</video>'
		elif dtype == 'flash':
			template = '<object data="%(src)s" type="application/x-shockwave-flash"></object>'
		else:
			template = '<object data="%(src)s"></object>'

		# TODO: make figures a command line option
		return '<figure>%s<figcaption>%s</figcaption></figure>' % (template % attributes, self.title.emit_html(**kwargs))

	def emit_latex(self, **kwargs) -> str:
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

	def emit_jd(self, **kwargs) -> str:
		title_text = self.title.emit_jd(**kwargs)
		title = ' "' + title_text + '"' if title_text else ''
		return '![%s](%s%s)' % (self.alt.emit_jd(**kwargs), self.src, title)


class ImplicitLink(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<a href="%s" class="implicit">%s</a>' % (self.text, self.text)

	def emit_rtf(self, **kwargs) -> str:
		return r'''{\field{\*\fldinst{HYPERLINK "%s"
}}{\fldrslt{\ul
%s
}}}''' % (self.text, self.text)

	def emit_latex(self, **kwargs) -> str:
		return r' \url{%s}' % self.text


class ImplicitEmail(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<a href="mailto:%s" class="implicit">%s</a>' % (self.text, self.text)

	def emit_rtf(self, **kwargs) -> str:
		return r'''{\field{\*\fldinst{HYPERLINK "mailto:%s"
}}{\fldrslt{\ul
%s
}}}''' % (self.text, self.text)

	def emit_latex(self, **kwargs) -> str:
		return r'\href{mailto:%s}{%s}' % (self.text, self.text)


# For text ----------------------------------------------------------------------

class Plaintext(TextNode):
	pass

# TODO: Shouldn't this be a text node?
class CodeInline(Node):
	def emit_html(self, **kwargs) -> str:
		return '<code>%s</code>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\texttt{%s}' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '`%s`' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Emph(Node):
	def emit_html(self, **kwargs) -> str:
		return '<em>%s</em>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'{\i %s}' % ''.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\textit{%s}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '*%s*' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Strong(Node):
	def emit_html(self, **kwargs) -> str:
		return '<strong>%s</strong>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'{\b %s}' % ''.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\textbf{%s}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '**%s**' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class StrongEmph(Node):
	def emit_html(self, **kwargs) -> str:
		return '<strong><em>%s</em></strong>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'{\b \i %s}' % ''.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\textit{\textbf{%s}}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '***%s***' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Strikethrough(Node):
	def emit_html(self, **kwargs) -> str:
		return '<del>%s</del>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_rtf(self, **kwargs) -> str:
		return r'{\strike %s\par}' % r'\line '.join(i.emit_rtf(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '~~%s~~' % ''.join(i.emit_jd(**kwargs) for i in self.children)


# MATH -------------------

class MathInline(Node):
	def emit_html(self, **kwargs) -> str:
		return '<span class="math">%s</span>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		text = ''.join(i.emit_latex(**kwargs) for i in self.children)
		for regex, subst in latex_math_subst:
			text = text.replace(regex, subst)
		return '$%s$' % text

	def emit_jd(self, **kwargs) -> str:
		return '«%s»' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Parenthesis(Node):
	def emit_html(self, **kwargs) -> str:
		return '(%s)' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs) -> str:
		return '<mfenced open="(" close=")"><mrow>%s</mrow></mfenced>' % ''.join(i.emit_mathml(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return '(%s)' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '(%s)' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Braces(Node):
	def emit_html(self, **kwargs) -> str:
		return '{}' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\{%s\}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '{%s}' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Brackets(Node):
	def emit_html(self, **kwargs) -> str:
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs) -> str:
		return ''.join(i.emit_mathml(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '[%s]' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Sum(Node):
	# TODO: emit_mathml
	def emit_html(self, **kwargs) -> str:
		return '''
	<math><mstyle displaystyle="true"><mrow>
	<munderover>
		<mo>&sum;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></mstyle></math>
	%s
	''' % (
			self.children[0].emit_mathml(**kwargs),
			self.children[1].emit_mathml(**kwargs),
			''.join(i.emit_html(**kwargs) for i in self.children[2:]),
		)

	def emit_latex(self, **kwargs) -> str:
		return r'\displaystyle\sum^{%s}_{%s} %s' % (
			self.children[1].emit_latex(**kwargs),
			self.children[0].emit_latex(**kwargs),
			''.join(i.emit_latex(**kwargs) for i in self.children[2:]),
		)

	def emit_jd(self, **kwargs) -> str:
		return r'sum[%s %s %s]' % (
			self.children[0].emit_jd(**kwargs),
			self.children[1].emit_jd(**kwargs),
			''.join(i.emit_jd(**kwargs) for i in self.children[2:]),
		)


class Prod(Node):
	#TODO: emit_mathml
	def emit_html(self, **kwargs) -> str:
		return '''
	<math><mstyle displaystyle="true"><mrow>
	<munderover>
		<mo>&prod;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></mstyle></math>
	%s
	''' % (
			self.children[0].emit_mathml(**kwargs),
			self.children[1].emit_mathml(**kwargs),
			''.join(i.emit_html(**kwargs) for i in self.children[2:]),
		)

	def emit_latex(self, **kwargs) -> str:
		return r'\displaystyle\prod^{%s}_{%s} %s' % (
			self.children[1].emit_latex(**kwargs),
			self.children[0].emit_latex(**kwargs),
			''.join(i.emit_latex(**kwargs) for i in self.children[2:]),
		)

	def emit_jd(self, **kwargs) -> str:
		return r'prod[%s %s %s]' % (
			self.children[0].emit_jd(**kwargs),
			self.children[1].emit_jd(**kwargs),
			''.join(i.emit_jd(**kwargs) for i in self.children[2:]),
		)


class Int(Node):
	# TODO: emit_mathml
	def emit_html(self, **kwargs) -> str:
		return '''
	<math><mstyle displaystyle="true"><mrow>
	<munderover>
		<mo>&int;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></mstyle></math>
	%s
	''' % (
			self.children[0].emit_mathml(**kwargs),
			self.children[1].emit_mathml(**kwargs),
			''.join(i.emit_html(**kwargs) for i in self.children[2:]),
		)

	def emit_latex(self, **kwargs) -> str:
		return r'\displaystyle\sum^{%s}_{%s} %s' % (
			self.children[1].emit_latex(**kwargs),
			self.children[0].emit_latex(**kwargs),
			''.join(i.emit_latex(**kwargs) for i in self.children[2:]),
		)

	def emit_jd(self, **kwargs) -> str:
		return r'int[%s %s %s]' % (
			self.children[0].emit_jd(**kwargs),
			self.children[1].emit_jd(**kwargs),
			''.join(i.emit_jd(**kwargs) for i in self.children[2:]),
		)

class Sqrt(Node):
	def emit_html(self, **kwargs) -> str:
		return '√<span style="border-top: 1px solid">%s</span>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs) -> str:
		return '<msqrt>%s</msqrt>' % ''.join(i.emit_mathml(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return r'\sqrt{%s}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return r'sqrt[%s]' % ''.join(i.emit_jd(**kwargs) for i in self.children)


#TODO: Properly nest Subscript and Superscript nodes, having both the base and "exponent"

class SuperscriptBrackets(Node):
	def emit_html(self, **kwargs) -> str:
		return '<sup>%s</sup>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs):
		return '<msup><msrow></msrow><msrow>%s</msrow></mssup>' % ''.join(i.emit_mathml(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return '^{%s}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '^[%s]' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class SubscriptBrackets(Node):
	def emit_html(self, **kwargs) -> str:
		return '<sub>%s</sub>' % ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs) -> str:
		return '<msub><msrow></msrow><msrow>%s</msrow></mssub>' % ''.join(i.emit_mathml(**kwargs) for i in self.children)

	def emit_latex(self, **kwargs) -> str:
		return '_{%s}' % ''.join(i.emit_latex(**kwargs) for i in self.children)

	def emit_jd(self, **kwargs) -> str:
		return '_[%s]' % ''.join(i.emit_jd(**kwargs) for i in self.children)


class Subscript(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<sub>%s</sub>' % html.escape(self.text, quote=True)

	def emit_mathml(self, **kwargs) -> str:
		return '<msub><mrow></mrow><mrow>%s</mrow></mssub>' % html.escape(self.text, quote=True)

	def emit_latex(self, **kwargs) -> str:
		return '_{%s}' % self.text

	def emit_jd(self, **kwargs) -> str:
		return '_%s' % self.text


class Superscript(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<sup>%s</sup>' % html.escape(self.text, quote=True)

	def emit_mathml(self, **kwargs) -> str:
		return '<msup><mrow></mrow><mrow>%s</mrow></mssup>' % html.escape(self.text, quote=True)

	def emit_latex(self, **kwargs) -> str:
		return '^{%s}' % self.text

	def emit_jd(self, **kwargs) -> str:
		return '^%s' % self.text


class Identifier(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<em>%s</em>' % html.escape(self.text, quote=True)

	def emit_mathml(self, **kwargs) -> str:
		return '<mi>%s</mi>' % self.text


class Operator(TextNode):
	def emit_html(self, **kwargs) -> str:
		return ' %s ' % html.escape(self.text, quote=True)

	def emit_mathml(self, **kwargs) -> str:
		return '<mo>%s</mo>' % self.text


class Comment(TextNode):
	def emit_html(self, **kwargs) -> str:
		return ' %s ' % html.escape(self.text, quote=True)

	def emit_latex(self, **kwargs) -> str:
		return r' \text{%s}' % self.text

	def emit_jd(self, **kwargs) -> str:
		return ' # %s # ' % self.text


class Number(TextNode):
	def emit_mathml(self, **kwargs) -> str:
		return '<mn>%s</mn>' % self.text


class Newline(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<br>'

	def emit_latex(self, **kwargs) -> str:
		return r'\\'

	def emit_jd(self, **kwargs) -> str:
		return '\n'
