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
			return res


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
		return "<li>" + ''.join(i.emit_html() for i in self.children) + "</li>"


class Paragraph(Node):
	def emit_html(self):
		return "<p>" + "<br>".join(i.emit_html() for i in self.children) + "</p>"


class CodeBlock(Node):
	def emit_html(self):
		return "<pre><code>" + ''.join(i.emit_html() for i in self.children) + "</code></pre>"


class MathBlock(Node):
	def emit_html(self):
		return "<blockquote>" + "<br>".join(i.emit_html() for i in self.children) + "</blockquote>"


class Text(Node):
	def emit_html(self):
		return ''.join(i.emit_html() for i in self.children)


class Math(Node):
	def emit_html(self):
		return ''.join(i.emit_html() for i in self.children)


# For text -------------------------

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


# MATH -------------------

class MathInline(Node):
	def emit_html(self):
		return "<q>" + ''.join(i.emit_html() for i in self.children) + "</q>"


class Parenthesis(Node):
	def emit_html(self):
		return "(" + ''.join(i.emit_html() for i in self.children) + ")"


class Braces(Node):
	def emit_html(self):
		return "{" + ''.join(i.emit_html() for i in self.children) + "}"


class Brackets(Node):
	def emit_html(self):
		return "[" + ''.join(i.emit_html() for i in self.children) + "]"


class SuperscriptParens(Node):
	def emit_html(self):
		return "<sup>" + ''.join(i.emit_html() for i in self.children) + "</sup>"


class SubscriptParens(Node):
	def emit_html(self):
		return "<sub>" + ''.join(i.emit_html() for i in self.children) + "</sub>"


class Subscript(TextNode):
	def emit_html(self):
		return "<sub>" + html.escape(self.text, quote=True) + "</sub>"


class Superscript(TextNode):
	def emit_html(self):
		return "<sup>" + html.escape(self.text, quote=True) + "</sup>"


class Identifier(TextNode):
	def emit_html(self):
		return "<strong><em>" + html.escape(self.text, quote=True) + "</em></strong>"


class Operator(TextNode):
	def emit_html(self):
		return " %s " % html.escape(self.text, quote=True)


class Comment(TextNode):
	def emit_html(self):
		return ' ' + html.escape(self.text, quote=True)


class Number(TextNode):
	pass


class Newline(TextNode):
	def emit_html(self):
		return "<br>"