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

To parse a single jotdown file (suggested extension: `.jd`), use `jd`:

    $ jd <input_file.jd> [-o <output_file>] [-f <format>] [-s <stylesheet>]
    
The `-o`, `f`, and `-s` parameters are optional. The output filename will be `out` if one is not specified. The default output format is HTML. The default stylesheet is the included Solarized-based theme.

To export a whole directory structure of jotdown files, just pass a directory to `jd`:

    $ jd <directory> [-o <output_directory>] [-f <format>] [-s <stylesheet>]

The `directory` structure will be replicated under `output_directory`, and all `.jd` files will be translated to the specified output format. Links to other `.jd` files are automatically converted to the correct file extension. The stylesheet file will be copied to `output_directory` and all output documents will link to it instead of embedding its text. Other files found in side `directory` will be copied over verbatim. This mode allows, for example, to have a source tree for a website including Jotdown source documents, custom HTML, images, etc. that will be exported with a single command, to a single directory that is ready to be deployed.

A note on encodings
-------------------

The provided sample document (`text.jd`) is encoded as UTF-8, and so it will work unmodified only on systems where UTF-8
is default, as Python will use the system's default encoding for reading files. Jotdown could be hard-coded to read files
as UTF-8, but I chose not to because a user's `.jd` files will presumably be in their system's encoding of choice.
Because of this, reading your own `.jd` files you edited as plaintext should work with no issues on any system.

HTML output, however, *is* hard-coded to be UTF-8. Jotdown's output files are not intended to be modified by hand, so it
should not be a problem. A `<meta charset="UTF-8">` tag is included in every generated HTML file, so any reasonable
browser will be able to handle it, special characters and all.

Output formats
--------------

Jotdown is designed to support output in many different formats. At the time, HTML output is supported (which includes a bit of MathML), as well as a debug mode that allows for inspection of the parse tree. LATEX output is planned, but work has not yet started.

Output style
------------

Jotdown includes CSS files that will be embedded in every HTML document to style them. The default stylesheet, `solarized.css` is based on the
[Solarized](http://ethanschoonover.com/solarized) color scheme for maximum readability. A stylesheet is also included to mimic the look of IEEE publications (`ieee.css`), to test and demontstrate Jotdown's readiness for use as a source language in scientific manuscripts.

Browser compatibility
---------------------

Some math-related features (namely capital-sigma notation for sums, capital-pi notation for products, and integrals) do
not have a clean way to be marked up as HTML. For this reason, they are output as MathML inside `<math>` tags. MathML is
supported by Firefox, Opera and Safari, but not by Chrome. Chrome users, be warned. All other expressions are kept as
pure HTML for maximum compatibility.
