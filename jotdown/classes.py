# -*- coding: utf-8 -*-
import html

# Abstract ---------------------------------
import jotdown.globalv as globalv


class Node():
	def __init__(self, children=None):
		self.children = children if children else []


class TextNode(Node):
	def __init__(self, text):
		super().__init__()
		self.text = text

	def emit_html(self, **kwargs):
		return html.escape(self.text, quote=True)

# For blocks -------------------------------------------------------------------------


class Document(Node):
	def __init__(self, children=None, name="Jotdown Document"):
		super().__init__(children)
		self.name = name

	def emit_html(self, css, **kwargs):
		with open(css) as style:
			res = "<!DOCTYPE html><html><head><title>%s</title><meta charset=\"UTF-8\"><style>%s</style></head><body>"\
			      % (self.name, style.read())
			res += '\n'.join(block.emit_html(**kwargs) for block in self.children)
			if kwargs['ref_style']:
				res += '<footer>' + ReferenceList().emit_html(**kwargs) + '</footer>'
			res += "</body></html>"
			return res.encode('utf-8')


class Heading(Node):
	def emit_html(self, **kwargs):
		return "<h1>" + '<br>'.join(i.emit_html(**kwargs) for i in self.children) + "</h1>"


class Subheading(Node):
	def emit_html(self, **kwargs):
		return "<h2>" + '<br>'.join(i.emit_html(**kwargs) for i in self.children) + "</h2>"


class HorizontalRule(Node):
	def emit_html(self, **kwargs):
		return "<hr/>"


class List(Node):
	pass


class UList(List):
	def emit_html(self, **kwargs):
		res = "<ul>"
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += "</ul>"
		return res


class OList(List):
	def __init__(self, children=None, start=1):
		super().__init__(children)
		self.start = start

	def emit_html(self, **kwargs):
		res = "<ol start=\"%s\">" % self.start
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += "</ol>"
		return res


class ReferenceList(OList):
	def __init__(self):
		items = [ReferenceItem(ref_key, content[0]) for ref_key, content in globalv.references.items()]
		super().__init__(items, 1)

	def emit_html(self, **kwargs):
		res = '<ol class="references" start="%s">' % self.start
		for item in self.children:
			res += item.emit_html(**kwargs)
		res += '</ol>'
		return res


class ListItem(Node):
	def emit_html(self, **kwargs):
		res = ["<li><span>", ''.join(i.emit_html(**kwargs) for i in self.children[:-1])]

		if len(self.children) > 0 and isinstance(self.children[-1], List):
			res.append("</span>" + self.children[-1].emit_html(**kwargs))
		elif len(self.children) > 0:
			res.append(self.children[-1].emit_html(**kwargs) + "</span>")

		return ''.join(res)


class ReferenceItem(Node):
	def __init__(self, ref_key, content):
		self.ref_key = ref_key
		self.content = content
		super().__init__()

	def emit_html(self, **kwargs):
		return '<li><a id="%s"><span>%s</span></a></li>' % (self.ref_key, self.content.emit_html(**kwargs))


class Paragraph(Node):
	def emit_html(self, **kwargs):
		return "<p>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</p>"


class CodeBlock(Node):
	def emit_html(self, **kwargs):
		return "<code class=\"console\">" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</code>"


class MathBlock(Node):
	def emit_html(self, **kwargs):
		return "<div class='math'>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</div>"


class Blockquote(Node):
	def emit_html(self, **kwargs):
		return "<blockquote>" + "<br>".join(i.emit_html(**kwargs) for i in self.children) + "</blockquote>"


class Text(Node):
	def emit_html(self, **kwargs):
		return ''.join(i.emit_html(**kwargs) for i in self.children)


class Math(Node):
	def emit_html(self, **kwargs):
		return ''.join(i.emit_html(**kwargs) for i in self.children)


class Table(Node):
	def emit_html(self, **kwargs):
		return "<table>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</table>"


class TableRow(Node):
	def emit_html(self, **kwargs):
		return "<tr>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</tr>"


class TableHeader(Node):
	def emit_html(self, **kwargs):
		return "<th>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</th>"


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
		return "<td style=\"text-align: %s;\">" % self.align_map[self.align] +\
		       ''.join(i.emit_html(**kwargs) for i in self.children) + "</td>"


class Link(TextNode):
	def __init__(self, text, url):
		super().__init__(text)
		self.url = url

	def emit_html(self, **kwargs):
		return "<a href=\"" + self.url + "\">" + self.text + "</a>"


class ReferenceLink(TextNode):
	def __init__(self, text, ref_key):
		super().__init__(text)
		self.ref_key = ref_key

	def emit_html(self, ref_style=False, **kwargs):
		if not globalv.references[self.ref_key]:
			raise Exception("Missing definition for reference '%s'" % self.ref_key)
		if ref_style:
			place = list(globalv.references.keys()).index(self.ref_key) + 1
			return '%s<cite>[<a href="#%s">%d</a>]</cite>' % (self.text, self.ref_key, place)
		else:
			_, href = globalv.references[self.ref_key]
			return '<a href="%s">%s</a>' % (html.escape(href), self.text)


class Image(Node):
	def __init__(self, alt, src, title, children=None):
		super().__init__(children)
		self.alt = alt
		self.src = src
		self.title = title

	def emit_html(self, **kwargs):
		return "<img src=\"%s\" title=\"%s\" alt=\"%s\">" % (self.src, self.title, self.alt)


class ImplicitLink(TextNode):
	def emit_html(self, **kwargs):
		return "<a href=\"" + self.text + "\">" + self.text + "</a>"


class ImplicitEmail(TextNode):
	def emit_html(self, **kwargs):
		return "<a href=\"mailto:" + self.text + "\">" + self.text + "</a>"


# For text ----------------------------------------------------------------------

class Plaintext(TextNode):
	pass


class CodeInline(Node):
	def emit_html(self, **kwargs):
		return "<code>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</code>"


class Emph(Node):
	def emit_html(self, **kwargs):
		return "<em>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</em>"


class Strong(Node):
	def emit_html(self, **kwargs):
		return "<strong>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</strong>"


class StrongEmph(Node):
	def emit_html(self, **kwargs):
		return "<strong><em>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</em></strong>"


class Strikethrough(Node):
	def emit_html(self, **kwargs):
		return "<del>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</del>"


# MATH -------------------

class MathInline(Node):
	def emit_html(self, **kwargs):
		return '<span class="math">' + ''.join(i.emit_html(**kwargs) for i in self.children) + '</q>'


class Parenthesis(Node):
	def emit_html(self, **kwargs):
		return "(" + ''.join(i.emit_html(**kwargs) for i in self.children) + ")"

	def emit_mathml(self, **kwargs):
		return "<mfenced open=\"(\" close=\")\"><mrow>" + ''.join(i.emit_mathml(**kwargs) for i in self.children)\
		       +"</mrow></mfenced>"


class Braces(Node):
	def emit_html(self, **kwargs):
		return "{ " + ''.join(i.emit_html(**kwargs) for i in self.children) + " }"


class Brackets(Node):
	def emit_html(self, **kwargs):
		return ''.join(i.emit_html(**kwargs) for i in self.children)

	def emit_mathml(self, **kwargs):
		return ''.join(i.emit_mathml(**kwargs) for i in self.children)


class Sum(Node):
	def emit_html(self, **kwargs):
		#return "∑"
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


class SuperscriptBrackets(Node):
	def emit_html(self, **kwargs):
		return "<sup>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</sup>"

	def emit_mathml(self, **kwargs):
		return "<msup><msrow></msrow><msrow>" + ''.join(i.emit_mathml(**kwargs) for i in self.children) + "</msrow></mssup>"


class SubscriptBrackets(Node):
	def emit_html(self, **kwargs):
		return "<sub>" + ''.join(i.emit_html(**kwargs) for i in self.children) + "</sub>"

	def emit_mathml(self, **kwargs):
		return "<msub><msrow></msrow><msrow>" + ''.join(i.emit_mathml(**kwargs) for i in self.children) + "</msrow></mssub>"


class Subscript(TextNode):
	def emit_html(self, **kwargs):
		return "<sub>" + html.escape(self.text, quote=True) + "</sub>"

	def emit_mathml(self, **kwargs):
		return "<msub><mrow></mrow><mrow>" + html.escape(self.text, quote=True) + "</mrow></mssub>"


class Superscript(TextNode):
	def emit_html(self, **kwargs):
		return "<sup>" + html.escape(self.text, quote=True) + "</sup>"

	def emit_mathml(self, **kwargs):
		return "<msup><mrow></mrow><mrow>" + html.escape(self.text, quote=True) + "</mrow></mssup>"


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


class Number(TextNode):
	def emit_mathml(self, **kwargs):
		return "<mn>" + self.text + "</mn>"


class Newline(TextNode):
	def emit_html(self, **kwargs):
		return "<br>"
