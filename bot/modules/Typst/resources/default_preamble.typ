#import "typograph.typ": *
#fc.update((
  main: (font: ("New Computer Modern", "Source Han Serif")),
  sans: (font: ("New Computer Modern Sans", "Source Han Sans")),
  mono: (font: ("Latin Modern Mono")),
  math: (font: "New Computer Modern Math"),
  size: 12pt,
))


#set par(
  justify: true,
  justification-limits: (tracking: (min: -0.075em, max: 0.075em)),
  first-line-indent: (
    amount: 0em,
  ),
  hanging-indent: 0pt,
  leading: 0.9em,
  spacing: 0.9em
)

