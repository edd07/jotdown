# "Macro" regexes for math tokens
math_exp = {
	'op': r"\+\*/%=↔→←≈∼≠≟<≤≥>∴∈∉⊂⊄⊆⊈…!±−,:|∀∧∨⊕¬∩∪Ø",
	'num': r'\d∞\.',
	'not_id': r'\W_',
	'not_letter': r'\W\d_',
	'parens': r'\(\)\{\}\[\]'
}

# Regex used for only substituting something if it's its own word
word_re = r"(?:\b|(?<=[%(not_letter)s]))" % math_exp + \
          "%s" + "(?:\b|(?=[%(not_letter)s]))" % math_exp

math_subst = [
# Greek alphabet
(word_re % "ALPHA", 'Α'),
(word_re % "BETA", 'Β'),
(word_re % "GAMMA", 'Γ'),
(word_re % "DELTA", 'Δ'),
(word_re % "EPSILON", 'Ε'),
(word_re % "ZETA", 'Ζ'),
(word_re % "ETA", 'Η'),
(word_re % "THETA", 'Θ'),
(word_re % "IOTA", 'Ι'),
(word_re % "KAPPA", 'Κ'),
(word_re % "LAMBDA", 'Λ'),
(word_re % "MU", 'Μ'),
(word_re % "NU", 'Ν'),
(word_re % "XI", 'Ξ'),
(word_re % "OMICRON", 'Ο'),
(word_re % "PI", 'Π'),
(word_re % "RHO", 'Ρ'),
(word_re % "SIGMA", 'Σ'),
(word_re % "TAU", 'Τ'),
(word_re % "YPSILON", 'Υ'),
(word_re % "PHI", 'Φ'),
(word_re % "CHI", 'Χ'),
(word_re % "PSI", 'Ψ'),
(word_re % "OMEGA", 'Ω'),
(word_re % "alpha", 'α'),
(word_re % "beta", 'β'),
(word_re % "gamma", 'γ'),
(word_re % "delta", 'δ'),
(word_re % "epsilon", 'ε'),
(word_re % "zeta", 'ζ'),
(word_re % "eta", 'η'),
(word_re % "theta", 'θ'),
(word_re % "iota", 'ι'),
(word_re % "kappa", 'κ'),
(word_re % "lambda", 'λ'),
(word_re % "mu", 'μ'),
(word_re % "nu", 'ν'),
(word_re % "xi", 'ξ'),
(word_re % "omicron", 'ο'),
(word_re % "pi", 'π'),
(word_re % "rho", 'ρ'),
(word_re % "sigma", 'σ'),
(word_re % "tau", 'τ'),
(word_re % "ypsilon", 'υ'),
(word_re % "phi", 'φ'),
(word_re % "chi", 'χ'),
(word_re % "psi", 'ψ'),
(word_re % "omega", 'ω'),

# Number sets
(word_re % "NATURALS", 'ℕ'),
(word_re % "INTEGERS", 'ℤ'),
(word_re % "RATIONALS", 'ℚ'),
(word_re % "REALS", 'ℝ'),
(word_re % "COMPLEX", 'ℂ'),

# Infinities
(word_re % "INF", '∞'),
(word_re % "ALEPH", 'ℵ'),

# Logic
(word_re % "AND", '∧'),
(word_re % "OR", '∨'),
(word_re % "XOR", '⊕'),

# Relation operators
(r"<->", '↔'),
(r"->", '→'),
(r"<-", '←'),
(r"~=", '≈'),
(r"~", '∼'),
(r"!=", '≠'),
(r"\?=", '≟'),
(r"<=", '≤'),
(r">=", '≥'),
(r":\.|\.:", '∴'),

# Sets
(r"€", '∈'),
(r"!€", '∉'),
(r"!©=", '⊈'),
(r"!©", '⊄'),
(r"©=", '⊆'),
(r"©", '⊂'),
(r"ø", '∅'),
(r"[Ĉĉ]", "^∁"),
(word_re % "UNION", '∪'),
(word_re % "INTERSECTION", '∩'),
(word_re % "EMPTY", 'Ø'),

# More operators
(r"\.\.\.", '…'),
(r"\+-", '±'),
(r"-", '−'),

# Quantification
(word_re % "FORALL", '∀'),
(word_re % "!EXISTS", '∄'),
(word_re % "EXISTS", '∃')
]