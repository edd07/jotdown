Jotdown
=======

Compiler for a Markdown-like syntax intended for note-taking. Jotdown is:

* Pretty in plaintext
* Easily and quickly typable while, say, taking a class
* Version-controllable
* Ünì©ôðé-friendly
* Translatable to HTML, but theoretically to anything else
* Capable of parsing some elements of math formulas for pretty output with human-readable syntax
* A Python 3 program

Usage
-----

To parse a single jotdown file (suggested extension: `.jd`), use `parser.py`:

    $ python3 parser.py <input_file.jd> <output_file.html>

Support for parsing a directory structure and generating index pages is planned but not yet implemented.

A note on encodings
-------------------

The provided sample document (`text.jd`) is encoded as UTF-8, and so it will work unmodified only on systems where UTF-8
is default, as Python will use the system's default encoding for reading files. Jotdown could be hard-coded to read files
as UTF-8, but I chose not to because a user's `.jd` files will presumably be in their system's encoding of choice.
Because of this, reading your own `.jd` files you edited as plaintext should work with no issues on any system.

HTML output, however, *is* hard-coded to be UTF-8. Jotdown's output files are not intended to be modified by hand, so it
should not be a problem. A `<meta charset="UTF-8">` tag is included in every generated HTML file, so any reasonable
browser will be able to handle it, special characters and all.

Browser compatibility
---------------------

Some math-related features (namely capital-sigma notation for sums, capital-pi notation for products, and integrals) do
not have a clean way to be marked up as HTML. For this reason, they are output as MathML inside `<math>` tags. MathML is
supported by Firefox, Opera and Safari, but not by Chrome. Chrome users, be warned. All other expressions are kept as
pure HTML for maximum compatibility.

Output style
------------

Jotdown includes a `style.css` file that will be embedded in every HTML document in `<style>` tags. This file can be
edited to produce any document style the user wants. By default, it uses a stylesheet based on the
[Solarized](http://ethanschoonover.com/solarized) color scheme for maximum readability.
