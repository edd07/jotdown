from re import compile

from jotdown.globalv import re_flags

# "Macro" regexes for math tokens
math_exp = {
	'op': r'\+\*/%%=↔→←≈∼≠≟<≤≥>∴∈∉⊂⊄⊆⊈…!±−,:|∀∧∨⊕¬∩∪Ø',
	'num': r'\d∞\.',
	'not_id': r'\W_',
	'not_letter': r'\W\d_',
	'parens': r'\(\)\{\}\[\]'
}

# Regex used for only substituting something if it's its own word
word_re = r'(?:\b|(?<=[%(not_letter)s]))%%s(?:\b|(?=[%(not_letter)s]))' % math_exp

math_subst = [
# Greek alphabet
(word_re % 'ALPHA', 'Α'),
(word_re % 'BETA', 'Β'),
(word_re % 'GAMMA', 'Γ'),
(word_re % 'DELTA', 'Δ'),
(word_re % 'EPSILON', 'Ε'),
(word_re % 'ZETA', 'Ζ'),
(word_re % 'ETA', 'Η'),
(word_re % 'THETA', 'Θ'),
(word_re % 'IOTA', 'Ι'),
(word_re % 'KAPPA', 'Κ'),
(word_re % 'LAMBDA', 'Λ'),
(word_re % 'MU', 'Μ'),
(word_re % 'NU', 'Ν'),
(word_re % 'XI', 'Ξ'),
(word_re % 'OMICRON', 'Ο'),
(word_re % 'PI', 'Π'),
(word_re % 'RHO', 'Ρ'),
(word_re % 'SIGMA', 'Σ'),
(word_re % 'TAU', 'Τ'),
(word_re % 'YPSILON', 'Υ'),
(word_re % 'PHI', 'Φ'),
(word_re % 'CHI', 'Χ'),
(word_re % 'PSI', 'Ψ'),
(word_re % 'OMEGA', 'Ω'),
(word_re % 'alpha', 'α'),
(word_re % 'beta', 'β'),
(word_re % 'gamma', 'γ'),
(word_re % 'delta', 'δ'),
(word_re % 'epsilon', 'ε'),
(word_re % 'zeta', 'ζ'),
(word_re % 'eta', 'η'),
(word_re % 'theta', 'θ'),
(word_re % 'iota', 'ι'),
(word_re % 'kappa', 'κ'),
(word_re % 'lambda', 'λ'),
(word_re % 'mu', 'μ'),
(word_re % 'nu', 'ν'),
(word_re % 'xi', 'ξ'),
(word_re % 'omicron', 'ο'),
(word_re % 'pi', 'π'),
(word_re % 'rho', 'ρ'),
(word_re % 'sigma', 'σ'),
(word_re % 'tau', 'τ'),
(word_re % 'ypsilon', 'υ'),
(word_re % 'phi', 'φ'),
(word_re % 'chi', 'χ'),
(word_re % 'psi', 'ψ'),
(word_re % 'omega', 'ω'),

# Number sets
	(word_re % 'NATURALS', 'ℕ'),
	(word_re % 'INTEGERS', 'ℤ'),
	(word_re % 'RATIONALS', 'ℚ'),
	(word_re % 'REALS', 'ℝ'),
	(word_re % 'COMPLEX', 'ℂ'),

# Infinities
(word_re % 'INF', '∞'),
(word_re % 'ALEPH', 'ℵ'),

# Logic
(word_re % 'AND', '∧'),
(word_re % 'OR', '∨'),
(word_re % 'XOR', '⊕'),

# Relation operators
(r'<->', '↔'),
(r'->', '→'),
(r'<-', '←'),
(r'~=', '≈'),
(r'~', '∼'),
(r'!=', '≠'),
(r'\?=', '≟'),
(r'<=', '≤'),
(r'>=', '≥'),
(r':\.|\.:', '∴'),

# Sets
(r'€', '∈'),
(r'!€', '∉'),
(r'!©=', '⊈'),
(r'!©', '⊄'),
(r'©=', '⊆'),
(r'©', '⊂'),
(r'ø', '∅'),
(r'[Ĉĉ]', '^∁'),
(word_re % 'UNION', '∪'),
(word_re % 'INTERSECTION', '∩'),
(word_re % 'EMPTY', 'Ø'),

# More operators
(r'\.\.\.', '…'),
(r'\+-', '±'),
(r'-', '−'),

# Quantification
(word_re % 'FORALL', '∀'),
(word_re % '!EXISTS', '∄'),
(word_re % 'EXISTS', '∃')
]

math_subst = [(compile(exp, flags=re_flags), val) for (exp, val) in math_subst]

latex_math_subst = [
# Greek alphabet
('Α', r'\Alpha '),
('Β', r'\Beta '),
('Γ', r'\Gamma '),
('Δ', r'\Delta '),
('Ε', r'\Epsilon '),
('Ζ', r'\Zeta '),
('Η', r'\Eta '),
('Θ', r'\Theta '),
('Ι', r'\Iota '),
('Κ', r'\Kappa '),
('Λ', r'\Lambda '),
('Μ', r'\Mu '),
('Ν', r'\Nu '),
('Ξ', r'\Xi '),
('Ο', r'\Omicron '),
('Π', r'\Pi '),
('Ρ', r'\Rho '),
('Σ', r'\Sigma '),
('Τ', r'\Tau '),
('Υ', r'\Ypsilon '),
('Φ', r'\Phi '),
('Χ', r'\Xi '),
('Ψ', r'\Psi '),
('Ω', r'\Omega '),
('α', r'\alpha '),
('β', r'\beta '),
('γ', r'\gamma '),
('δ', r'\delta '),
('ε', r'\varepsilon '),
('ζ', r'\zeta '),
('η', r'\nu '),
('θ', r'\theta '),
('ι', r'\iota '),
('κ', r'\kappa '),
('λ', r'\lambda '),
('μ', r'\mu '),
('ν', r'\nu '),
('ξ', r'\xi '),
('ο', r'\omicron '),
('π', r'\pi '),
('ρ', r'\rho '),
('σ', r'\sigma '),
('τ', r'\tau '),
('υ', r'\ypsilon '),
('φ', r'\psi '),
('χ', r'\xi '),
('ψ', r'\psi '),
('ω', r'\omega '),

# Number sets
('ℕ', r'\mathbb{N} '),
('ℤ', r'\mathbb{Z} '),
('ℚ', r'\mathbb{Q} '),
('ℝ', r'\mathbb{R} '),
('ℂ', r'\mathbb{C} '),

# Infinities
('∞', r'\infty '),
('ℵ', r'\aleph '),

# Logic
('∧', r'\wedge '),
('∨', r'\vee '),
('⊕', r'\oplus '),

# Relation operators
('↔', r'\leftrightarrow '),
('→', r'\rightarrow '),
('←', r'\leftarrow '),
('≈', r'\approx '),
('∼', r'\sim '),
('≠', r'\neq '),
('≟', r'\stackrel{?}{=} '),
('≤', r'\leq '),
('≥', r'\geq '),
('∴', r'\therefore '),

# Sets
('∈', r'\in '),
('∉', r'\notin '),
('⊈', r'\not\subseteq '),
('⊄', r'\not\subset '),
('⊆', r'\subseteq '),
('⊂', r'\subset '),
('∅', r'\varnothing '),
('∪', r'\cup '),
('∩', r'\cap '),
('Ø', r'\emptyset '),

# # More operators
# (r"\.\.\.", '…'),
# (r"\+-", '±'),
# (r"-", '−'),

# Quantification
('∀', r'\forall '),
('∄', r'\nexists '),
('∃', r'\exists ')
]

#latex_math_subst = [(compile(exp, flags=re_flags), val) for (exp, val) in latex_math_subst]