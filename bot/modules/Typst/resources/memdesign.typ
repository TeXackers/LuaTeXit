// Suppose we wanted the text blocks to be 2.3 times the width of a-z.
// Typst doesn't have \setlength like LaTeX, so we must define a custom width.
// 
#let mainfont = "New Computer Modern"
#let sansfont = "Fira Sans"
#let monofont = "JuliaMono"
#let mathfont = "TeX Gyre Pagella Math"
#let fontsize = 12pt

// size commands
// for now we will support fontsize classes for three default fontsizes: 10pt, 11pt, 12pt
// According to https://www.tug.org/TUGboat/tb33-3/tb105thurnherr.pdf
// (in order of tiny, scriptsize, footnotesize, small, normalsize, large, Large, LARGE, huge, Huge)
// 10: (5, 7, 8, 9, 10, 12, 14, 17, 20, 25)
// 11: (6, 8, 9, 10, 11, 12, 14, 17, 20, 25)
// 12: (6, 8, 10, 10, 12, 14, 17, 20, 25, 25)


// shape variants
#let tf(x) = text(x, font: mainfont, weight: "regular", size: fontsize)
#let it(x) = text(x, style: "italic")
#let sl(x) = text(x, style: "oblique")
#let bf(x) = text(x, weight: "bold")
#let bi(x) = text(x, style: "italic", weight: "bold")
#let bs(x) = text(x, style: "oblique", weight: "bold")
#let sc(x) = text(x, features: ("smcp", "cpsp"), tracking: fontsize*0.06)

// typeface variants
#let rm(x) = text(x, font: mainfont)
#let sf(x) = text(x, font: sansfont)
#let tt(x) = text(x, font: monofont)

// LATEX logo
#let LaTeX = {
  let A = (
    offset: (
      x: -0.33em,
      y: -0.3em,
    ),
    size: 0.7em,
  )
  let T = (
    x_offset: -0.12em    
  )
  let E = (
    x_offset: -0.2em,
    y_offset: 0.23em,
    size: 1em
  )
  let X = (
    x_offset: -0.1em
  )
  [L#h(A.offset.x)#text(size: A.size, baseline: A.offset.y)[A]#h(T.x_offset)T#h(E.x_offset)#text(size: E.size, baseline: E.y_offset)[E]#h(X.x_offset)X]
}

#show "LaTeX": name => LaTeX


// show how references are formatted (<section>.<number>)
#show heading.where(level:1): it => {
  // counter(math.equation).update(0)
  counter(table).update(0)
  [#it]
}

#set figure(numbering: it => {
  let count = counter(heading.where(level: 1)).at(here()).first()
  if count > 0 and start_section_numbering_at_0 {
    numbering("1.1", count + 1, it)
  }
  else {
    numbering("1.1", count + 1, it)
  }
})

// #set figure(supplement: "")


#show ref: iter => {
  let eq = math.equation
  let el = iter.element
  if (el != none) and el.func() == eq {
    numbering(
      el.numbering,
      ..counter(eq).at(el.location())
    )
  } else { iter }
}

// set link colour
#show ref: set text(fill: rgb(67, 152, 184))
#show link: set text(fill: rgb(39, 153, 61))
#show cite: set text(fill: rgb(39, 153, 61))


// set font
#set text(font: mainfont, size: fontsize, hyphenate: false, features: ("lnum", ))
#set par(
  justify: true,
  justification-limits: (tracking: (min: -0.075em, max: 0.075em)),
  first-line-indent: 4em / 3,
  hanging-indent: 0pt,
  leading: 1.15em,
  spacing: 1.15em
)
#show math.equation: set text(font: mathfont, size: fontsize, hyphenate: false)