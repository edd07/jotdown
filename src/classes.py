# -*- coding: utf-8 -*-
import html

# Abstract ---------------------------------


class Node():
	def __init__(self, children=None):
		self.children = children if children else []


class TextNode(Node):
	def __init__(self, text, children=None):
		super().__init__(children)
		self.text = text

	def emit_html(self):
		return html.escape(self.text, quote=True)

# For blocks ----------------------------------


class Document(Node):
	def emit_html(self):
		with open("src/style.css") as style:
			res = "<html><head><meta charset=\"UTF-8\"><style>%s</style></head><body>" % style.read()
			for block in self.children:
				res += block.emit_html()
			res += "<body></html>"
			return res.encode('utf-8')


class Heading(Node):
	def emit_html(self):
		return "<h1>" + '<br>'.join(i.emit_html() for i in self.children) + "</h1>"


class Subheading(Node):
	def emit_html(self):
		return "<h2>" + '<br>'.join(i.emit_html() for i in self.children) + "</h2>"


class UList(Node):
	def emit_html(self):
		res = "<ul>"
		for item in self.children:
			res += item.emit_html()
		res += "</ul>"
		return res


class OList(Node):
	def emit_html(self):
		res = "<ol>"
		for item in self.children:
			res += item.emit_html()
		res += "</ol>"
		return res


class ListItem(Node):
	def emit_html(self):
		return "<li><span>" + ''.join(i.emit_html() for i in self.children) + "</span></li>"


class Paragraph(Node):
	def emit_html(self):
		return "<p>" + "<br>".join(i.emit_html() for i in self.children) + "</p>"


class CodeBlock(Node):
	def emit_html(self):
		return "<pre><code class=\"console\">" + ''.join(i.emit_html() for i in self.children) + "</code></pre>"


class MathBlock(Node):
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
		return "<td align=\"%s\">" % self.align_map[self.align] +\
		       ''.join(i.emit_html() for i in self.children) + "</td>"


# For text -------------------------

class Plaintext(TextNode):
	pass


class CodeInline(Node):
	def emit_html(self):
		return "<pre><code>" + ''.join(i.emit_html() for i in self.children) + "</code></pre>"


class Emph(Node):
	def emit_html(self):
		return "<em>" + ''.join(i.emit_html() for i in self.children) + "</em>"


class Strong(Node):
	def emit_html(self):
		return "<strong>" + ''.join(i.emit_html() for i in self.children) + "</strong>"


class StrongEmph(Node):
	def emit_html(self):
		return "<strong><em>" + ''.join(i.emit_html() for i in self.children) + "</em></strong>"


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
		return "{" + ''.join(i.emit_html() for i in self.children) + "}"


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


class SuperscriptParens(Node):
	def emit_html(self):
		return "<sup>" + ''.join(i.emit_html() for i in self.children) + "</sup>"

	def emit_mathml(self):
		return "<msup><msrow></msrow><msrow>" + ''.join(i.emit_mathml() for i in self.children) + "</msrow></mssup>"


class SubscriptParens(Node):
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
		return "<strong><em>" + html.escape(self.text, quote=True) + "</em></strong>"

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