/// Dynamic font configuration
#let fc = state("fc", (
  main: (font: "New Computer Modern"),
  sans: (font: "New Computer Modern Sans"),
  mono: (font: "Latin Modern Mono"),
  math: (font: "New Computer Modern Math"),
  size: 12pt,
))

#let apply-fc(doc) = context {
  set text(
    font: fc.get().main.font,
    size: fc.get().size,
  )
  show math.equation: set text(
    font: fc.get().math.font,
    size: fc.get().size,
  )
  doc
}

/// "Primitives"
//  Typst has `h()`, but its abstraction may deter from semantically understanding the purpose of certain gauces of horizontal space.
//  Here we define common horizontal space primitives with more intuitive names.

// A space equal to the height of the em square (point size.) In early serifs, the metal face of the capital `М` tended to be square — probably, thus the English name. Metal type often used em space as paragraph indent.
#let emspace = context h(fc.get().size)
#let emsp = emspace

// Half of the width of an em. Russian-language metal type composition considered it the main type of space, even though in word spacing, especially if the text is aligned to the left or right, it is excessively wide.
#let enspace = context h(fc.get().size * 0.5)
#let ensp = enspace

// One third of an em space. Historically considered as the main space in Western European typography.
// 
// "The first obligation of a good typesetter is to achieve a compact line image, something best accomplished by using three-to-em or three-space word spacing. In former times even roman was set much tighter than we do it today; the specimen sheet that contains the original of Garamond’s roman of 1592, printed in 14-point, shows a word spacing in all lines of 2 points only, which is one-seventh of an em! This means that we cannot call three-to-em word spacing particularly tight."
// -- Jan Tschihold, The Form of The Book (1975)
#let thirdspace = context h(fc.get().size / 3)
#let thrsp = thirdspace

// One fourth of an em space. Some authors believe quarter space to be the primary word space.
// 
// For a normal text face in a normal text size, a typical value for the word space is a quarter of an em, which can be written M/4. (A quarter of an em is typically about the same as, or slightly more than, the set-width of the letter t.) 
// -- Robert Bringhurst, The Elements of Typographic Style (1992)
#let quarterspace = context h(fc.get().size / 4)
#let qtsp = quarterspace

// ⅕ of an em space. It is common that thin space equals about half the standard one, which is why thin space is used where standard word space would be too wide. For example, thin space is often utilised for spacing a dash in cases where standard space is too wide. Thin space is also used for spacing initials, from each other and from the surname:
#let thinspace = context h(fc.get().size / 5)
#let thinsp = thinspace

// The sixth space is used when the thin space is too large.
#let sixthspace = context h(fc.get().size / 6)
#let sixsp = sixthspace

// The narrowest of spaces. In metal type, it was equal to 1/10 of an em space, in the digital age it is mostly 1/ 24 of an em. It might be useful if a certain typeface’s punctuation marks have too tight sidebearings, but a thin space would be too wide. For example, you can use hair space to space dashes instead of thin one — everything depends on the sidebearings and the design of the particular typeface.
//
// You should keep in mind that after you change font, selected space glyphs will remain, but their width can change, — and this will affect the texture.
#let hairspace = context h(fc.get().size / 10)
#let hairsp = hairspace

// Combination of em dash and hairspaces.
//
// Note that with some fonts, an Em dash comes with sidebearings sufficient to eliminate the need for additional space glyphs, which will not warrant the use of this definition.
#show "\u{2015}": hairspace + "\u{2015}" + hairspace
#show "\u{2014}": hairspace + "\u{2014}" + hairspace

// Figure space, or numeric space, is used for typesetting tables and sheets. If a typeface is fitted with tabular figures, its figure space will be equal to the width of tabular figures. Figure space is a non-breaking one.
// Requesting the "tnum" feature makes the measurement match tabular figures where the font has them; where it doesn't, "tnum" is a no-op and this falls back to the width of the default "0".
#let figurespace = context h(measure(text(
  "0",
  font: fc.get().main.font,
  features: ("tnum",),
  size: fc.get().size,
)).width)
#let figsp = figurespace




/// Font shape and typeface variants
/// These are mostly inspired by ConTeXt
#let tf(x) = context text(x, font: fc.get().main.font, weight: "regular", size: fc.get().size)
#let it(x) = text(x, style: "italic")
#let sl(x) = text(x, style: "oblique")
#let bf(x) = text(x, weight: "bold")
#let bi(x) = text(x, style: "italic", weight: "bold")
#let bs(x) = text(x, style: "oblique", weight: "bold")
#let sc(x) = context text(x, features: ("smcp": 1, "cpsp": 1), tracking: fc.get().size * 0.06)

/// typeface variants
#let rm(x) = context text(x, font: fc.get().main.font)
#let sf(x) = context text(x, font: fc.get().sans.font)
#let tt(x) = context text(x, font: fc.get().mono.font)

/// fontsizes
// ranging from tiny, scriptsize, footnotesize, small, normalsize, large, Large, LARGE, huge, Huge
// should scale with respect to normalsize
// we support 8~12 points as normalsizes, so we can write a dictionary

#let font_size_scheme = (
  "8": (
    tiny: 4pt,
    scriptsize: 5pt,
    footnotesize: 6pt,
    small: 7pt,
    normalsize: 8pt,
    large: 9pt,
    Large: 10pt,
    LARGE: 10.95pt,
    huge: 12pt,
    Huge: 14.4pt
  ),
  "9": (
    tiny: 5pt,
    scriptsize: 6pt,
    footnotesize: 7pt,
    small: 8pt,
    normalsize: 9pt,
    large: 10pt,
    Large: 10.95pt,
    LARGE: 12pt,
    huge: 14.4pt,
    Huge: 17.28pt
  ),
  "10": (
    tiny: 5pt,
    scriptsize: 7pt,
    footnotesize: 8pt,
    small: 9pt,
    normalsize: 10pt,
    large: 10.95pt,
    Large: 12pt,
    LARGE: 14.4pt,
    huge: 17.28pt,
    Huge: 20.74pt
  ),
  "11": (
    tiny: 6pt,
    scriptsize: 8pt,
    footnotesize: 9pt,
    small: 10pt,
    normalsize: 10.95pt,
    large: 12pt,
    Large: 14.4pt,
    LARGE: 17.28pt,
    huge: 20.74pt,
    Huge: 24.88pt
  ),
  "12": (
    tiny: 6pt,
    scriptsize: 8pt,
    footnotesize: 10pt,
    small: 10.95pt,
    normalsize: 12pt,
    large: 14.4pt,
    Large: 17.28pt,
    LARGE: 20.74pt,
    huge: 24.88pt,
    Huge: 24.88pt
  ),
)

#let calc_font_size(normalsize, scale) = (
	if str(normalsize.pt()) in font_size_scheme {
		font_size_scheme.at(str(normalsize.pt())).at(scale)
	} else {
		if scale == "tiny" {
			calc.max(normalsize - 4pt, normalsize / 2)
		} else if scale == "scriptsize" {
			normalsize - 3pt
		} else if scale == "footnotesize" {
			normalsize - 2pt
		} else if scale == "small" {
			normalsize - 1pt
		} else if scale == "normalsize" {
			normalsize
		} else if scale == "large" {
			calc.max(normalsize * calc.pow(1.2, 0.5), normalsize + 1pt)
		} else if scale == "Large" {
			calc.max(normalsize * calc.pow(1.2, 1), normalsize + 2pt)
		} else if scale == "LARGE" {
			calc.max(normalsize * calc.pow(1.2, 2), normalsize + 3pt)
		} else if scale == "huge" {
			calc.max(normalsize * calc.pow(1.2, 3), normalsize + 4pt)
		} else if scale == "Huge" {
			if normalsize > 12pt {
				calc.max(normalsize * calc.pow(1.2, 3), normalsize + 4pt)
			} else {
			calc.max(normalsize * calc.pow(1.2, 4), normalsize + 5pt)
			}
		}
	}
)

#let tiny(x) = context text(x, size: calc_font_size(fc.get().size, "tiny"))
#let scriptsize(x) = context text(x, size: calc_font_size(fc.get().size, "scriptsize"))
#let footnotesize(x) = context text(x, size: calc_font_size(fc.get().size, "footnotesize"))
#let small(x) = context text(x, size: calc_font_size(fc.get().size, "small"))
#let normalsize(x) = context text(x, size: fc.get().size)
#let large(x) = context text(x, size: calc_font_size(fc.get().size, "large"))
#let Large(x) = context text(x, size: calc_font_size(fc.get().size, "Large"))
#let LARGE(x) = context text(x, size: calc_font_size(fc.get().size, "LARGE"))
#let huge(x) = context text(x, size: calc_font_size(fc.get().size, "huge"))
#let Huge(x) = context text(x, size: calc_font_size(fc.get().size, "Huge"))