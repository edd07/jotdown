class Node():
	def __init__(self, children=None):
		self.children = children if children else []


class Document(Node):
	def emit_html(self):
		res = "<html><body>"
		for block in self.children:
			res += block.emit_html()
		res += "<body></html>"
		return res


class Heading(Node):
	def __init__(self, text, children=None):
		super().__init__(children)
		self.text = text

	def emit_html(self):
		return "<h1>" + self.text + "</h1>"


class Subheading(Node):
	def __init__(self, text, children=None):
		super().__init__(children)
		self.text = text

	def emit_html(self):
		return "<h2>" + self.text + "</h2>"


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
	def __init__(self, text, children=None):
		super().__init__(children)
		self.text = text

	def emit_html(self):
		return "<li>" + self.text + "</li>"


class Paragraph(Node):
	def __init__(self, text, children):
		super().__init__(children)
		self.text = text

	def emit_html(self):
		return "<p>" + self.text + "</p>"