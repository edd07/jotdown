# Abstract ---------------------------------

class Node():
	def __init__(self, children=None):
		self.children = children if children else []


class TextNode(Node):
	def __init__(self, text, children=None):
		super().__init__(children)
		self.text = text

# For blocks ----------------------------------

class Document(Node):
	def emit_html(self):
		res = "<html><body>"
		for block in self.children:
			res += block.emit_html()
		res += "<body></html>"
		return res


class Heading(TextNode):
	def emit_html(self):
		return "<h1>" + '<br>'.join(self.text) + "</h1>"


class Subheading(TextNode):
	def emit_html(self):
		return "<h2>" + '<br>'.join(self.text) + "</h2>"


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


class Paragraph(TextNode):
	def emit_html(self):
		return "<p>" + "<br>".join(self.text) + "</p>"


class CodeBlock(TextNode):
	def emit_html(self):
		return "<pre><code>" + ''.join(self.text) + "</code></pre>"


# For text -------------------------

class CodeInline(TextNode):
	def emit_html(self):
		return "<code>" + ''.join(self.text) + "</code>"


class Emph(TextNode):
	def emit_html(self):
		return "<em>" + ''.join(self.text) + "</em>"


class Strong(TextNode):
	def emit_html(self):
		return "<strong>" + ''.join(self.text) + "</strong>"