Jotdown
=======

Compiler for a Markdown-like syntax intended for note-taking. Jotdown is:

* Based on the [Markdown](http://daringfireball.net/projects/markdown/) format
* Pretty and readable in plain-text
* Version-controllable documents
* Ünì©ôðé-friendly
* A language for math formulas like: «e^[i pi] + 1 = 0»
* Translatable to HTML, LATEX, RTF, and extensible for other formats
* Open source

Usage
-----

To parse a single jotdown file (suggested extension: `.jd`), use `jd`:

    $ jd <input_file.jd> [-o <output_file>] [-f <format>] [-s <stylesheet>]
    
The `-o`, `f`, and `-s` parameters are optional. The output filename will be `out` if one is not specified. The default output format is HTML. The default stylesheet is the included Solarized-based theme.

To export a whole directory structure of jotdown files, just pass a directory to `jd`:

    $ jd <directory> [-o <output_directory>] [-f <format>] [-s <stylesheet>]

The `directory` structure will be replicated under `output_directory`, and all `.jd` files will be translated to the specified output format. Links to other `.jd` files are automatically converted to the correct file extension. The stylesheet file will be copied to `output_directory` and all output documents will link to it instead of embedding its text. Other files found in side `directory` will be copied over verbatim. This mode allows, for example, to have a source tree for a website including Jotdown source documents, custom HTML, images, etc. that will be exported with a single command, to a single directory that is ready to be deployed.

### Other options

    $ jd <input> [-o <output>] [-f <format>] [-s <stylesheet>] [-r | --md-refs]

* `-r` or `--md-refs`: Treat citation-style links in a manner compatible with Markdown. Jotdown's own behaviour (allowing markup inside citations, not only links) is default.
* `-a` or `--author`: Specify an author for the compiled document. Defaults to the system's current user name.
A note on encodings
-------------------

The provided sample document (`text.jd`) is encoded as UTF-8, and so it will work unmodified only on systems where UTF-8 is default, as Python will use the system's default encoding for reading files. Jotdown could be hard-coded to read files as UTF-8, but I chose not to because a user's `.jd` files will presumably be in their system's encoding of choice.

Because of this, reading your own `.jd` files you edited as plaintext should work with no issues on any system.

Output, however, *is* hard-coded, most likely to UTF-8 (depending on the format). Jotdown's output files are not intended to be modified by hand, so their encoding should not be a problem. A `<meta charset="UTF-8">` tag is included in every generated HTML file, so any reasonable browser will be able to handle it, special characters and all.

Output formats
--------------

Jotdown is designed to support output in many different formats. At the time, HTML output is supported (which includes a bit of MathML), as well as a debug mode that allows for inspection of the parse tree. LATEX output is planned, but work has not yet started.

Output style
------------

Jotdown includes CSS files that will be embedded in every HTML document to style them. The default stylesheet, `solarized.css` is based on the [Solarized](http://ethanschoonover.com/solarized) color scheme for maximum readability. A stylesheet is also included to mimic the look of IEEE publications (`ieee.css`), to test and demontstrate Jotdown's readiness for use as a source language in scientific manuscripts.

Browser compatibility
---------------------

Some math-related features (namely capital-sigma notation for sums, capital-pi notation for products, and integrals) do not have a clean way to be marked up as HTML. For this reason, they are output as MathML inside `<math>` tags. MathML is supported by Firefox, Opera and Safari, but not by Chrome. Chrome users, be warned. All other expressions are kept as pure HTML for maximum compatibility.
