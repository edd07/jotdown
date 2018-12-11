# -*- coding: utf-8 -*-
import html
import os
import re
from getpass import getuser
from socket import gethostname
from typing import Sequence, Iterable
import logging

import jotdown.globalv as globalv
from jotdown.regex import latex_math_subst


# Abstract ---------------------------------
class Node:
	def __init__(self, children: Iterable['Node']=None) -> None:
		self.children = children if children else []

	def join_children(self, string: str, fmt: str, **kwargs) -> str:
		return string.join(getattr(i, f'emit_{fmt}')(**kwargs) for i in self.children)

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
		res += self.join_children('', 'debug', indent=indent + 1)
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

	def emit_html(self, stylesheet: str, ref_style: bool=False, embed_css: bool=True, **kwargs) -> str:
		if embed_css:
			css_string = f'<style>{globalv.read_with_encoding(stylesheet)}</style>'
		else:
			css_string = f'<link rel="stylesheet" href="{stylesheet}"/>'

		body = self.join_children('\n', 'html', ref_style=ref_style)
		# TODO: Author and creation time meta tags
		return f'''<!DOCTYPE html><html>
<head>
<title>{self.name}</title>
<meta charset="UTF-8">{css_string}
</head>
<body>
{body}
<footer>{ReferenceList().emit_html(ref_style=True, **kwargs) if ref_style else ""}</footer>
</body>
</html>
'''

	def emit_rtf(self, stylesheet: str, **kwargs) -> str:
		# TODO: Author in info, and create time
		return rf'''{{\rtf1\ansi\deff0\widowctrl {globalv.read_with_encoding(stylesheet)}
{{\info
{{\title {self.name}}}
{{\author PLACEHOLDER}}
{{\creatim\yr2016\mo7\dy20\hr18\min37}}
}}
{self.join_children("", "rtf", **kwargs)}
}}
'''

	def emit_latex(self, stylesheet: str, ref_style: bool=False, **kwargs) -> str:
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
			'body': self.join_children('', 'latex', ref_style=ref_style, **kwargs),
			'references': ReferenceList().emit_latex(ref_style=True, **kwargs) if ref_style else '',
			'author': self.author,
			'institution': self.hostname,
		}
		return globalv.read_with_encoding(stylesheet) % field_dict


class Heading(Node):
	def __init__(self, level: int, children: Sequence[Node]=None) -> None:
		super().__init__(children)
		self.level = min(level, 6)

	def emit_html(self, **kwargs) -> str:
		# Sanitize the text for the id
		ident = self.join_children('', 'html', **kwargs).strip()
		ident = re.sub(r'<[^>]*>', '', ident, flags=globalv.re_flags)
		ident = re.sub(r'\s', '-', ident, flags=globalv.re_flags)
		ident = html.escape(ident)

		# Make sure it's unique on the whole document
		while ident in globalv.html_document_ids:
			ident += '_'
		globalv.html_document_ids.add(ident)

		return f'<h{self.level} id="{ident}">{self.join_children("<br>", "html", **kwargs)}</h{self.level}>'

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
		body = self.join_children(r'\line', 'rtf', **kwargs)
		return rf'{{\pard\sa180\sb90\keepn\s{styles[self.level]} {body}\par}}'

	def emit_latex(self, **kwargs) -> str:
		levels = {
			1: r'\section{',
			2: r'\subsection{',
			3: r'\subsubsection{',
		}
		body = r'\\'.join(i.emit_latex(**kwargs) for i in self.children)
		return levels.get(self.level, rf'\subsubsection{{{body}}}\n')

	def emit_jd(self, **kwargs) -> str:
		# TODO: Emit the other style of heading canonically?
		return f'{"#" * self.level} {self.join_children("", "jd", **kwargs)}\n\n'


class HorizontalRule(Node):
	def emit_html(self, **kwargs) -> str:
		return '<hr/>'

	def emit_latex(self, **kwargs) -> str:
		return '\n' r'\rule{\textwidth}{1pt}' '\n'

	def emit_jd(self, **kwargs) -> str:
		return '---\n\n'


class ListNode(Node):
	pass


class UList(ListNode):
	def emit_html(self, **kwargs) -> str:
		return f'<ul>{"".join(i.emit_html(**kwargs) for i in self.children)}</ul>'

	def emit_latex(self, **kwargs) -> str:
		return rf'''\begin{{itemize}}
{self.join_children("", "latex", **kwargs)}
\end{{itemize}}
'''

	def emit_jd(self, depth: int=0, **kwargs) -> str:
		list_res = []
		for list_item in self.children:
			list_item_res = []
			for node in list_item.children:
					list_item_res.append(node.emit_jd(depth=depth + 1, **kwargs))
			list_res.append('\t' * depth + f'* {"".join(list_item_res)}')
		return '\n'.join(list_res) + ('\n' if depth == 0 else '')


class OList(ListNode):
	def __init__(self, children: Sequence[Node]=None, list_type: str='1', start: int=1) -> None:
		super().__init__(children)
		self.start = start
		self.list_type = list_type

	def emit_html(self, **kwargs) -> str:
		return f'<ol start="{self.start}" type="{self.list_type}">\
		{self.join_children("", "html", **kwargs)}</ol>'

	def emit_latex(self, **kwargs) -> str:
		return rf'''\begin{{enumerate}}
{self.join_children("", "latex", **kwargs)}
\end{{enumerate}}'''

	def emit_jd(self, depth: int=0, **kwargs) -> str:
		list_res = []
		for n, list_item in enumerate(self.children):
			list_item_res = []
			for node in list_item.children:
				list_item_res.append(node.emit_jd(depth=depth + 1, **kwargs))
			# TODO: Support the other list types
			list_res.append('\t' * depth + str(n + 1) + f' {"".join(list_item_res)}')
		return '\n'.join(list_res) + ('\n' if depth == 0 else '')


class CheckList(UList):
	def emit_html(self, **kwargs) -> str:
		return f'<ul class="checklist">{self.join_children("", "html", **kwargs)}</ul>'


class ReferenceList(OList):
	def __init__(self) -> None:
		items = [ReferenceItem(ref_key, content[0]) for ref_key, content in globalv.references.items()]
		super().__init__(items, '1')

	def emit_html(self, **kwargs) -> str:
		return f'<ol class="references" start="{self.start}">{self.join_children("", "html", **kwargs)}</ol>'

	def emit_latex(self, **kwargs) -> str:
		body = "\n".join(i.emit_latex(**kwargs) for i in self.children)
		return rf'''\begin{{thebibliography}}{{{len(globalv.references)}}}
{body}
\end{{thebibliography}}
'''


class ListItem(Node):
	def emit_html(self, **kwargs) -> str:
		res = [f'<li><span>{"".join(i.emit_html(**kwargs) for i in self.children[:-1])}']

		if self.children and isinstance(self.children[-1], ListNode):
			res.append(f'</span>{self.children[-1].emit_html(**kwargs)}')
		elif self.children:
			res.append(f'{self.children[-1].emit_html(**kwargs)}</span>')

		return ''.join(res)

	def emit_latex(self, **kwargs) -> str:
		return rf'\item {self.join_children("", "latex", **kwargs)}\n'


class ChecklistItem(Node):
	def __init__(self, checked: bool, children: Sequence[Node]=None):
		self.checked = checked
		super().__init__(children)

	def emit_html(self, **kwargs) -> str:
		css_class = 'checked' if self.checked else 'unchecked'
		res = [f'<li class="{css_class}"><span>{"".join(i.emit_html(**kwargs) for i in self.children[:-1])}']

		if self.children and isinstance(self.children[-1], ListNode):
			res.append(f'</span>{self.children[-1].emit_html(**kwargs)}')
		elif self.children:
			res.append(f'{self.children[-1].emit_html(**kwargs)}</span>')

		return ''.join(res)


class ReferenceItem(Node):
	def __init__(self, ref_key, content) -> None:
		self.ref_key = ref_key
		self.content = content
		super().__init__()

	def emit_html(self, **kwargs) -> str:
		return f'<li><a id="self.ref_key"><span>{self.content.emit_html(**kwargs)}</span></a></li>'

	def emit_latex(self, **kwargs) -> str:
		return rf'\bibitem{{{self.ref_key}}} {self.content.emit_latex(**kwargs)} '


class Paragraph(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<p>{self.join_children("<br>", "html", **kwargs)}</p>'

	def emit_rtf(self, **kwargs) -> str:
		return r'{\pard\s1 %s\par}' % self.join_children(r'\line', 'rtf', **kwargs)

	def emit_latex(self, **kwargs) -> str:
		return r'\par %s' % self.join_children(r'\\ ', 'latex', **kwargs)

	def emit_jd(self, **kwargs) -> str:
		return f'{self.join_children("", "jd", **kwargs)} \n'


class CodeBlock(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<code class="console">{self.join_children("", "html", **kwargs)}</code>'

	def emit_rtf(self, **kwargs) -> str:
		body = self.join_children(r'\line ', 'rtf', **kwargs)
		return rf'''
{{\pard\sa180\li720\ri720\keep\f2
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
{body}
\par}}
'''

	def emit_latex(self, **kwargs) -> str:
		return rf'''\begin{{lstlisting}}
{self.join_children("", "latex", **kwargs)}
\end{{lstlisting}}
'''

	def emit_jd(self, **kwargs) -> str:
		return f'```\n{self.join_children("", "jd", **kwargs)}\n```'


class MathBlock(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<div class="math">{self.join_children("<br>", "html", **kwargs)}</div>'

	def emit_rtf(self, **kwargs) -> str:
		body = self.join_children(r'line ', 'rtf', **kwargs)
		return rf'''
{{\pard\sa180\li720\ri720\keep
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
{body}
\par}}
'''

	def emit_latex(self, **kwargs) -> str:
		body = self.join_children('\n', 'latex', **kwargs)
		return rf'''\begin{{gather*}}
{body}
\end{{gather*}}
'''

	def emit_jd(self, **kwargs) -> str:
		return f'«««\n{self.join_children("", "jd", **kwargs)}\n»»»'


class Blockquote(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<blockquote>{self.join_children("<br>", "html", **kwargs)}</blockquote>'

	def emit_rtf(self, **kwargs) -> str:
		body = self.join_children(r'\line ', 'rtf', **kwargs)
		return rf'''
{{\pard\sa180\li720\ri720\keep\f1
\brdrt\brdrs\brdrw10\brsp20
\brdrl\brdrs\brdrw10\brsp80
\brdrb\brdrs\brdrw10\brsp20
\brdrr\brdrs\brdrw10\brsp80
{body}
\par}}
'''

	def emit_latex(self, **kwargs) -> str:
		body = self.join_children(r'\\', 'latex', **kwargs)
		return rf'''\begin{{displayquote}}
{body}
\end{{displayquote}}
'''

	def emit_jd(self, **kwargs) -> str:
		return ''.join('>' + i.emit_jd(**kwargs) for i in self.children) + '\n'


class Math(Node):
	def emit_html(self, **kwargs) -> str:
		return self.join_children('', 'html', **kwargs)

	def emit_latex(self, **kwargs) -> str:
		text = self.join_children('', 'latex', **kwargs)
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
		caption_html = f'<caption>{"".join(i.emit_html(**kwargs) for i in self.caption)}</caption>' if self.caption else ''
		return f'''<table>
{caption_html}
<thead>{self.children[0].emit_html(**kwargs)}</thead>
<tbody>{"".join(i.emit_html(**kwargs) for i in self.children[1:])}</tbody>
</table>
'''

	def emit_latex(self, **kwargs) -> str:
		caption_latex = rf'\caption{{{"".join(i.emit_latex(**kwargs) for i in self.caption)}}}' if self.caption else ''
		alignment_string = f'{{{"|".join(self.latex_alignment_map[i] for i in self.alignment)}}}'
		body = ' \\\\\n'.join(i.emit_latex(**kwargs) for i in self.children[1:])

		return rf'''\begin{{table}}
{caption_latex}
\begin{{tabular}}{alignment_string}
{self.children[0].emit_latex(**kwargs)}\\ \hline
{body}
\end{{tabular}}
\end{{table}}
'''

	def emit_jd(self, **kwargs) -> str:
		return f'«{self.join_children("", "jd", **kwargs)}»'


class TableRow(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<tr>{self.join_children("", "html", **kwargs)}</tr>'

	def emit_latex(self, **kwargs) -> str:
		return self.join_children(' & ', 'latex', **kwargs)


class TableHeader(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<th>{self.join_children("", "html", **kwargs)}</th>'

	def emit_latex(self, **kwargs) -> str:
		return self.join_children('', 'latex', **kwargs)


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
		return f'<td style="text-align: {self.html_align_map[self.align]};">{self.join_children("", "html", **kwargs)}</td>'

	def emit_latex(self, **kwargs) -> str:
		return self.join_children('', 'latex', **kwargs)


class Link(Node):
	def __init__(self, linked_text: Node, url: str, ignore_link_translation: bool=False) -> None:
		# TODO: make this take a generic list of children instead of linked_text node
		super().__init__([linked_text])
		self.url = html.escape(url)
		self.linked_text = linked_text
		self.ignore_link_translation = ignore_link_translation

	def emit_html(self, link_translation: str=None, **kwargs) -> str:
		url = self.url
		if link_translation and not self.ignore_link_translation:
			url = globalv.ext_translation(url, link_translation)

		return f'<a href="{url}">{self.linked_text.emit_html(link_translation=link_translation, **kwargs)}</a>'

	def emit_rtf(self, link_translation: str=None, **kwargs) -> str:
		if link_translation and not self.ignore_link_translation:
			url = globalv.ext_translation(self.url, link_translation)
		else:
			url = self.url

		linked_cited = self.linked_text.emit_html(link_translation=link_translation, **kwargs)

		return rf'''{{\field{{\*\fldinst{{HYPERLINK "{url}"
}}}}{{\fldrslt{{\ul
{linked_cited}
}}}}}}'''

	def emit_latex(self, link_translation: str=None, **kwargs) -> str:
		url = self.url
		if link_translation and not self.ignore_link_translation:
			url = globalv.ext_translation(url, link_translation)
		return rf' \href{{{url}}}{{{self.linked_text.emit_latex(link_translation=link_translation, **kwargs)}}} '

	def emit_jd(self, **kwargs) -> str:
		# No extension translation needed when exporting to .jd
		return f'[{self.linked_text.emit_jd(**kwargs)}]({self.url})'


class ReferenceLink(Node):
	def __init__(self, cited_node: Node, ref_key: str) -> None:
		# TODO:  make this take a generic list of children instead of a singleton cited_node
		super().__init__([cited_node])
		self.cited_node = cited_node
		self.ref_key = ref_key

	def _check_ref_exists(self) -> None:
		if not globalv.references[self.ref_key]:
			raise Exception(f'Missing definition for reference "{self.ref_key}"')

	def emit_html(self, link_translation: str=None, ref_style: bool=False, **kwargs) -> str:
		self._check_ref_exists()

		if ref_style:
			place = list(globalv.references.keys()).index(self.ref_key) + 1
			emitted_html = self.cited_node.emit_html(
				link_translation=link_translation,
				ref_style=True,
				**kwargs
			)
			return f'{emitted_html}<cite>[<a href="#{self.ref_key}" class="reference">{place}</a>]</cite>'
		else:
			_, href = globalv.references[self.ref_key]
			href = html.escape(href)
			if link_translation:
				href = globalv.ext_translation(href, link_translation)
			return f'<a href="{href}">{self.cited_node}</a>'

	def emit_rtf(self, link_translation: str=None, ref_style: bool=False, **kwargs) -> str:
		self._check_ref_exists()

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
			return rf'{cited_emmited}{{\super\chftn}}{{\footnote\pard\plain\chftn {ref_emmited}}}'
		else:
			_, href = globalv.references[self.ref_key]
			href = html.escape(href)
			if link_translation:
				href = globalv.ext_translation(href, link_translation)
			return rf'''{{\field{{\*\fldinst{{HYPERLINK
"{href}"
}}}}{{\fldrslt{{\ul
{cited_emmited}
}}}}}}'''

	def emit_latex(self, link_translation: str=None, ref_style: bool=False, **kwargs) -> str:
		self._check_ref_exists()

		if ref_style:
			ref_emmited = self.cited_node.emit_latex(
				link_translation=link_translation,
				ref_style=True,
				**kwargs
			)
			return rf'{ref_emmited} \cite{{{self.ref_key}}}'
		else:
			_, href = globalv.references[self.ref_key]
			href = html.escape(href)
			if link_translation:
				href = globalv.ext_translation(href, link_translation)
			return rf' \href{{{href}}}{{{self.cited_node}}}'


class ImplicitLink(Link):
	def __init__(self, linked_text: Node, url: str) -> None:
		super().__init__(linked_text, url, ignore_link_translation=True)

	def emit_jd(self, **kwargs) -> str:
		return self.linked_text.emit_jd(**kwargs)


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
		return f'<figure>{template % attributes}<figcaption>{self.title.emit_html(**kwargs)}</figcaption></figure>'

	def emit_latex(self, **kwargs) -> str:
		dtype = globalv.content_filetypes(self.src)
		if dtype == 'image':
			elem = rf'\includegraphics[width=\textwidth]{{{self.src}}}'
		else:
			elem = ''

		return rf'''
\begin{{figure}}
\begin{{center}}
\caption{{{self.title}}}
{elem}
\end{{center}}
\end{{figure}}
'''

	def emit_jd(self, **kwargs) -> str:
		title_text = self.title.emit_jd(**kwargs)
		title = f' "{title_text}"' if title_text else ''
		return f'![{self.alt.emit_jd(**kwargs)}]({self.src}{title})'


# For text ----------------------------------------------------------------------


class Plaintext(TextNode):
	pass


# TODO: Shouldn't this be a text node?
class CodeInline(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<code>{self.join_children("", "html", **kwargs)}</code>'

	def emit_latex(self, **kwargs) -> str:
		return rf'\texttt{{{self.join_children("", "latex", **kwargs)}}}'

	def emit_jd(self, **kwargs) -> str:
		return f'`{self.join_children("", "jd", **kwargs)}`'


class Emph(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<em>{self.join_children("", "html", **kwargs)}</em>'

	def emit_rtf(self, **kwargs) -> str:
		return rf'{{\i {self.join_children("", "rtf", **kwargs)}}}'

	def emit_latex(self, **kwargs) -> str:
		return rf'\textit{{{self.join_children("", "latex", **kwargs)}}}'

	def emit_jd(self, **kwargs) -> str:
		return f'*{self.join_children("", "jd", **kwargs)}*'


class Strong(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<strong>{self.join_children("", "html", **kwargs)}</strong>'

	def emit_rtf(self, **kwargs) -> str:
		return rf'{{\b {self.join_children("", "rtf", **kwargs)}}}'

	def emit_latex(self, **kwargs) -> str:
		return rf'\textbf{{{self.join_children("", "latex", **kwargs)}}}'

	def emit_jd(self, **kwargs) -> str:
		return f'**{self.join_children("", "jd", **kwargs)}**'


class StrongEmph(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<strong><em>{self.join_children("", "html", **kwargs)}</em></strong>'

	def emit_rtf(self, **kwargs) -> str:
		return rf'{{\b \i {self.join_children("", "rtf", **kwargs)}}}'

	def emit_latex(self, **kwargs) -> str:
		return rf'\textit{{\textbf{{{self.join_children("", "latex", **kwargs)}}}}}'

	def emit_jd(self, **kwargs) -> str:
		return f'***{self.join_children("", "jd", **kwargs)}***'


class Strikethrough(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<del>{self.join_children("", "html", **kwargs)}</del>'

	def emit_rtf(self, **kwargs) -> str:
		body = self.join_children(r'\line ', 'rtf', **kwargs)
		return rf'{{\strike {body}\par}}'

	def emit_jd(self, **kwargs) -> str:
		return f'~~{self.join_children("", "jd", **kwargs)}~~'


# MATH -------------------

class MathInline(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<span class="math">{self.join_children("", "html", **kwargs)}</span>'

	def emit_latex(self, **kwargs) -> str:
		text = self.join_children("", "latex", **kwargs)
		for regex, subst in latex_math_subst:
			text = text.replace(regex, subst)
		return f'${text}$'

	def emit_jd(self, **kwargs) -> str:
		return f'«{self.join_children("", "jd", **kwargs)}»'


class Parenthesis(Node):
	def emit_html(self, **kwargs) -> str:
		return f'({self.join_children("", "html", **kwargs)})'

	def emit_mathml(self, **kwargs) -> str:
		return f'<mfenced open="(" close=")"><mrow>{self.join_children("", "mathml", **kwargs)}</mrow></mfenced>'

	def emit_latex(self, **kwargs) -> str:
		return f'({self.join_children("", "latex", **kwargs)})'

	def emit_jd(self, **kwargs) -> str:
		return f'({self.join_children("", "jd", **kwargs)})'


class Braces(Node):
	def emit_html(self, **kwargs) -> str:
		return f'{{{self.join_children("", "html", **kwargs)}}}'

	def emit_latex(self, **kwargs) -> str:
		return rf'\{{{self.join_children("", "latex", **kwargs)}\}}'

	def emit_jd(self, **kwargs) -> str:
		return f'{{{self.join_children("", "jd", **kwargs)}}}'


class Brackets(Node):
	def emit_html(self, **kwargs) -> str:
		return self.join_children("", "html", **kwargs)

	def emit_mathml(self, **kwargs) -> str:
		return self.join_children("", "mathml", **kwargs)

	def emit_jd(self, **kwargs) -> str:
		return f'[{self.join_children("", "jd", **kwargs)}]'


class CapitalNotation(Node):
	def _capital_notation_parts(self, fmt: str, **kwargs):
		lower = getattr(self.children[0], f'emit_{fmt}')(**kwargs)
		upper = getattr(self.children[1], f'emit_{fmt}')(**kwargs)
		terms = ''.join(getattr(i, f'emit_{fmt}')(**kwargs) for i in self.children[2:])
		return lower, upper, terms

	def _get_tag(self) -> str:
		return type(self).__name__.lower()

	def emit_html(self, **kwargs) -> str:
		logging.warning(
			f'Outputting MathML for {type(self).__name__} capital letter notation. MathML is not supported by Google Chrome.'
		)
		return f'<math>{self.emit_mathml(**kwargs)}</math>'

	def emit_mathml(self, **kwargs) -> str:
		lower, upper, terms = self._capital_notation_parts('mathml', **kwargs)
		return f'''
			<mstyle displaystyle="true"><mrow>
			<munderover>
				<mo>&{self._get_tag()};</mo>
				<mrow>{lower}</mrow><mrow>{upper}</mrow>
			</munderover>
			<mrow>{terms}</mrow>
			</mrow></mstyle>
			'''

	def emit_latex(self, **kwargs) -> str:
		lower, upper, terms = self._capital_notation_parts('latex', **kwargs)
		return rf'\displaystyle\{self._get_tag()}^{{{upper}}}_{{{lower}}} {terms}'

	def emit_jd(self, **kwargs) -> str:
		lower, upper, terms = self._capital_notation_parts('jd', **kwargs)
		return rf'{self._get_tag()}[{lower} {upper} {terms}]'


class Sum(CapitalNotation):
	pass


class Prod(CapitalNotation):
	pass


class Int(CapitalNotation):
	pass


class Sqrt(Node):
	def emit_html(self, **kwargs) -> str:
		return f'√<span style="border-top: 1px solid">{self.join_children("", "html", **kwargs)}</span>'

	def emit_mathml(self, **kwargs) -> str:
		return f'<msqrt>{self.join_children("", "mathml", **kwargs)}</msqrt>'

	def emit_latex(self, **kwargs) -> str:
		return rf'\sqrt{{{self.join_children("", "latex", **kwargs)}}}'

	def emit_jd(self, **kwargs) -> str:
		return rf'sqrt[{self.join_children("", "jd", **kwargs)}]'


# TODO: Properly nest Subscript and Superscript nodes, having both the base and "exponent"

class SuperscriptBrackets(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<sup>{self.join_children("", "html", **kwargs)}</sup>'

	def emit_mathml(self, **kwargs) -> str:
		return f'<msup><msrow></msrow><msrow>{self.join_children("", "mathml", **kwargs)}</msrow></mssup>'

	def emit_latex(self, **kwargs) -> str:
		return f'^{self.join_children("", "latex", **kwargs)}'

	def emit_jd(self, **kwargs) -> str:
		return f'^[{self.join_children("", "jd", **kwargs)}]'


class SubscriptBrackets(Node):
	def emit_html(self, **kwargs) -> str:
		return f'<sub>{self.join_children("", "html", **kwargs)}</sub>'

	def emit_mathml(self, **kwargs) -> str:
		return f'<msub><msrow></msrow><msrow>{self.join_children("", "mathml", **kwargs)}</msrow></mssub>'

	def emit_latex(self, **kwargs) -> str:
		return f'_{self.join_children("", "latex", **kwargs)}'

	def emit_jd(self, **kwargs) -> str:
		return f'_[{self.join_children("", "jd", **kwargs)}]'


class Subscript(TextNode):
	def emit_html(self, **kwargs) -> str:
		return f'<sub>{html.escape(self.text, quote=True)}</sub>'

	def emit_mathml(self, **kwargs) -> str:
		return f'<msub><mrow></mrow><mrow>{html.escape(self.text, quote=True)}</mrow></mssub>'

	def emit_latex(self, **kwargs) -> str:
		return f'_{self.text}'

	def emit_jd(self, **kwargs) -> str:
		return f'_{self.text}'


class Superscript(TextNode):
	def emit_html(self, **kwargs) -> str:
		return f'<sup>{html.escape(self.text, quote=True)}</sup>'

	def emit_mathml(self, **kwargs) -> str:
		return f'<msup><mrow></mrow><mrow>{html.escape(self.text, quote=True)}</mrow></mssup>'

	def emit_latex(self, **kwargs) -> str:
		return f'^{self.text}'

	def emit_jd(self, **kwargs) -> str:
		return f'^{self.text}'


class Identifier(TextNode):
	def emit_html(self, **kwargs) -> str:
		return f'<em>{html.escape(self.text, quote=True)}</em>'

	def emit_mathml(self, **kwargs) -> str:
		return f'<mi>{self.text}</mi>'


class Operator(TextNode):
	def emit_html(self, **kwargs) -> str:
		return f' {html.escape(self.text, quote=True)} '

	def emit_mathml(self, **kwargs) -> str:
		return f'<mo>{self.text}</mo>'


class Comment(TextNode):
	def emit_html(self, **kwargs) -> str:
		return f' {html.escape(self.text, quote=True)} '

	def emit_latex(self, **kwargs) -> str:
		return rf' \text{{{self.text}}}'

	def emit_jd(self, **kwargs) -> str:
		return f' # {self.text} # '


class Number(TextNode):
	def emit_mathml(self, **kwargs) -> str:
		return f'<mn>{self.text}</mn>'


class Newline(TextNode):
	def emit_html(self, **kwargs) -> str:
		return '<br>'

	def emit_latex(self, **kwargs) -> str:
		return r'\\'

	def emit_jd(self, **kwargs) -> str:
		return '\n'
