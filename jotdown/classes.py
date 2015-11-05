# -*- coding: utf-8 -*-
import html

# Abstract ---------------------------------


class Node():
	def __init__(self, children=None):
		self.children = children if children else []


class TextNode(Node):
	def __init__(self, text):
		super().__init__()
		self.text = text

	def emit_html(self):
		return html.escape(self.text, quote=True)

# For blocks -------------------------------------------------------------------------


class Document(Node):
	def __init__(self, children=None, name="Jotdown Document"):
		super().__init__(children)
		self.name = name

	def emit_html(self, style_fname):
		with open(style_fname) as style:
			res = "<!DOCTYPE html><html><head><title>%s</title><meta charset=\"UTF-8\"><style>%s</style></head><body>"\
			      % (self.name, style.read())
			res += '\n'.join(block.emit_html() for block in self.children)
			res += "</body></html>"
			return res.encode('utf-8')


class Heading(Node):
	def emit_html(self):
		return "<h1>" + '<br>'.join(i.emit_html() for i in self.children) + "</h1>"


class Subheading(Node):
	def emit_html(self):
		return "<h2>" + '<br>'.join(i.emit_html() for i in self.children) + "</h2>"


class HorizontalRule(Node):
	def emit_html(self):
		return "<hr/>"


class List(Node):
	pass


class UList(List):
	def emit_html(self):
		res = "<ul>"
		for item in self.children:
			res += item.emit_html()
		res += "</ul>"
		return res


class OList(List):
	def __init__(self, children=None, start=1):
		super().__init__(children)
		self.start = start

	def emit_html(self):
		res = "<ol start=\"%s\">" % self.start
		for item in self.children:
			res += item.emit_html()
		res += "</ol>"
		return res


class ListItem(Node):
	def emit_html(self):
		res = ["<li><span>", ''.join(i.emit_html() for i in self.children[:-1])]

		if len(self.children) > 0 and isinstance(self.children[-1], List):
			res.append("</span>" + self.children[-1].emit_html())
		elif len(self.children) > 0:
			res.append(self.children[-1].emit_html() + "</span>")

		return ''.join(res)


class Paragraph(Node):
	def emit_html(self):
		return "<p>" + "<br>".join(i.emit_html() for i in self.children) + "</p>"


class CodeBlock(Node):
	def emit_html(self):
		return "<code class=\"console\">" + ''.join(i.emit_html() for i in self.children) + "</code>"


class MathBlock(Node):
	def emit_html(self):
		return "<div class='math'>" + "<br>".join(i.emit_html() for i in self.children) + "</div>"


class Blockquote(Node):
	def emit_html(self):
		return "<blockquote>" + "<br>".join(i.emit_html() for i in self.children) + "</blockquote>"


class Text(Node):
	def emit_html(self):
		return ''.join(i.emit_html() for i in self.children)


class Math(Node):
	def emit_html(self):
		return ''.join(i.emit_html() for i in self.children)


class Table(Node):
	def emit_html(self):
		return "<table>" + ''.join(i.emit_html() for i in self.children) + "</table>"


class TableRow(Node):
	def emit_html(self):
		return "<tr>" + ''.join(i.emit_html() for i in self.children) + "</tr>"


class TableHeader(Node):
	def emit_html(self):
		return "<th>" + ''.join(i.emit_html() for i in self.children) + "</th>"


class TableCell(Node):
	align_map = {
		0: 'left',
	    1: 'center',
	    2: 'right'
	}

	def __init__(self, align, children=None):
		super().__init__(children=children)
		self.align = align

	def emit_html(self):
		return "<td style=\"text-align: %s;\">" % self.align_map[self.align] +\
		       ''.join(i.emit_html() for i in self.children) + "</td>"


class Link(TextNode):
	def __init__(self, text, url):
		super().__init__(text)
		self.url = url

	def emit_html(self):
		return "<a href=\"" + self.url + "\">" + self.text + "</a>"


class Image(Node):
	def __init__(self, alt, src, title, children=None):
		super().__init__(children)
		self.alt = alt
		self.src = src
		self.title = title

	def emit_html(self):
		return "<img src=\"%s\" title=\"%s\" alt=\"%s\">" % (self.src, self.title, self.alt)


class ImplicitLink(TextNode):
	def emit_html(self):
		return "<a href=\"" + self.text + "\">" + self.text + "</a>"


class ImplicitEmail(TextNode):
	def emit_html(self):
		return "<a href=\"mailto:" + self.text + "\">" + self.text + "</a>"


# For text ----------------------------------------------------------------------

class Plaintext(TextNode):
	pass


class CodeInline(Node):
	def emit_html(self):
		return "<code>" + ''.join(i.emit_html() for i in self.children) + "</code>"


class Emph(Node):
	def emit_html(self):
		return "<em>" + ''.join(i.emit_html() for i in self.children) + "</em>"


class Strong(Node):
	def emit_html(self):
		return "<strong>" + ''.join(i.emit_html() for i in self.children) + "</strong>"


class StrongEmph(Node):
	def emit_html(self):
		return "<strong><em>" + ''.join(i.emit_html() for i in self.children) + "</em></strong>"


class Strikethrough(Node):
	def emit_html(self):
		return "<del>" + ''.join(i.emit_html() for i in self.children) + "</del>"


# MATH -------------------

class MathInline(Node):
	def emit_html(self):
		return "<q>" + ''.join(i.emit_html() for i in self.children) + "</q>"


class Parenthesis(Node):
	def emit_html(self):
		return "(" + ''.join(i.emit_html() for i in self.children) + ")"

	def emit_mathml(self):
		return "<mfenced open=\"(\" close=\")\"><mrow>" + ''.join(i.emit_mathml() for i in self.children) + "</mrow></mfenced>"


class Braces(Node):
	def emit_html(self):
		return "{ " + ''.join(i.emit_html() for i in self.children) + " }"


class Brackets(Node):
	def emit_html(self):
		return ''.join(i.emit_html() for i in self.children)

	def emit_mathml(self):
		return ''.join(i.emit_mathml() for i in self.children)


class Sum(Node):
	def emit_html(self):
		#return "∑"
		return """
	<math><mrow>
	<munderover>
		<mo>&sum;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></math>
	""" % (self.children[0].emit_mathml(),
		   self.children[1].emit_mathml()) + ''.join(i.emit_html() for i in self.children[2:])


class Prod(Node):
	def emit_html(self):
		# return "∏"
		return """
	<math><mrow>
	<munderover>
		<mo>&prod;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></math>
	""" % (self.children[0].emit_mathml(),
		   self.children[1].emit_mathml()) + ''.join(i.emit_html() for i in self.children[2:])


class Int(Node):
	def emit_html(self):
		# return "∏"
		return """
	<math><mrow>
	<munderover>
		<mo>&int;</mo>
		<mrow>%s</mrow><mrow>%s</mrow>
	</munderover>
	<mrow></mrow>
	</mrow></math>
	""" % (self.children[0].emit_mathml(),
		   self.children[1].emit_mathml()) + ''.join(i.emit_html() for i in self.children[2:])


class SuperscriptBrackets(Node):
	def emit_html(self):
		return "<sup>" + ''.join(i.emit_html() for i in self.children) + "</sup>"

	def emit_mathml(self):
		return "<msup><msrow></msrow><msrow>" + ''.join(i.emit_mathml() for i in self.children) + "</msrow></mssup>"


class SubscriptBrackets(Node):
	def emit_html(self):
		return "<sub>" + ''.join(i.emit_html() for i in self.children) + "</sub>"

	def emit_mathml(self):
		return "<msub><msrow></msrow><msrow>" + ''.join(i.emit_mathml() for i in self.children) + "</msrow></mssub>"


class Subscript(TextNode):
	def emit_html(self):
		return "<sub>" + html.escape(self.text, quote=True) + "</sub>"

	def emit_mathml(self):
		return "<msub><mrow></mrow><mrow>" + html.escape(self.text, quote=True) + "</mrow></mssub>"


class Superscript(TextNode):
	def emit_html(self):
		return "<sup>" + html.escape(self.text, quote=True) + "</sup>"

	def emit_mathml(self):
		return "<msup><mrow></mrow><mrow>" + html.escape(self.text, quote=True) + "</mrow></mssup>"


class Identifier(TextNode):
	def emit_html(self):
		return "<em>" + html.escape(self.text, quote=True) + "</em>"

	def emit_mathml(self):
		return "<mi>" + self.text + "</mi>"


class Operator(TextNode):
	def emit_html(self):
		return " %s " % html.escape(self.text, quote=True)

	def emit_mathml(self):
		return "<mo>" + self.text + "</mo>"


class Comment(TextNode):
	def emit_html(self):
		return ' %s ' % html.escape(self.text, quote=True)


class Number(TextNode):
	def emit_mathml(self):
		return "<mn>" + self.text + "</mn>"


class Newline(TextNode):
	def emit_html(self):
		return "<br>"