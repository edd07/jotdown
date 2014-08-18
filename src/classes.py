# Abstract ---------------------------------


class Node():
	def __init__(self, children=None):
		self.children = children if children else []


class TextNode(Node):
	def __init__(self, text, children=None):
		super().__init__(children)
		self.text = text

	def emit_html(self):
		return self.text

# For blocks ----------------------------------


class Document(Node):
	def emit_html(self):
		res = "<html><body>"
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


class ListItem(TextNode):
	def emit_html(self):
		return "<li>" + self.text + "</li>"


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


class Math(Text):
	pass


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


class Subscript(TextNode):
	def emit_html(self):
		return "<sub>" + self.text + "</sub>"


class Superscript(TextNode):
	def emit_html(self):
		return "<sup>" + self.text + "</sup>"


class Identifier(TextNode):
	def emit_html(self):
		return "<strong>" + self.text + "</strong>"


class Operator(TextNode):
	pass