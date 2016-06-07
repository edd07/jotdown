from collections import OrderedDict
import re

references = OrderedDict()  # References for citation mode
html_document_ids = set()  # Set of strings that are ids to certain html elements

re_flags = re.UNICODE