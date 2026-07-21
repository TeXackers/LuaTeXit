// we define negative spacing here

#let muskip(amount: 1) = { h((1em / 18) * amount) }
#let thinmuskip = { muskip(amount: 3) }
#let medmuskip = { muskip(amount: 4) }
#let thickmuskip = { muskip(amount: 5) }
#let quad = { muskip(amount: 18) }
#let qquad = { muskip(amount: 36) }

#let negmuskip = { muskip(amount: -1) }
#let negthinmuskip = { muskip(amount: -3) }
#let negmedmuskip = { muskip(amount: -4) }
#let negthickmuskip = { muskip(amount: -5) }
#let negquad = { muskip(amount: -18) }
#let negqquad = { muskip(amount: -36) }

// Opening symbols (mathopen)

// Left parenthesis
#let lparen = symbol("\u{0028}")
// Left square bracket
#let lbrack = symbol("\u{005B}")
// Left curly bracket
#let lbrace = symbol("\u{007B}")
// Radical
#let sqrt = symbol("\u{221A}")
// Cube root
#let cbrt = symbol("\u{221B}")
// Cube root
#let cuberoot = cbrt
// Fourth root
#let fourthroot = symbol("\u{221C}")
// Left ceiling
#let lceil = symbol("\u{2308}")
// Left floor
#let lfloor = symbol("\u{230A}")
// Upper-left corner
#let ulcorner = symbol("\u{231C}")
// Lower-left corner
#let llcorner = symbol("\u{231E}")
// Upper left or lower right curly bracket section
#let lmoustache = symbol("\u{23B0}")
// Light left tortoise shell bracket ornament
#let lbrbrak = symbol("\u{2772}")
// Left S-shaped bag delimiter
#let lbag = symbol("\u{27C5}")
// Long division
#let longdivision = symbol("\u{27CC}")
// Mathematical left white square bracket
#let lBrack = symbol("\u{27E6}")
// Mathematical left angle bracket
#let langle = symbol("\u{27E8}")
// Mathematical left double angle bracket
#let lAngle = symbol("\u{27EA}")
// Mathematical left white tortoise shell bracket
#let Lbrbrak = symbol("\u{27EC}")
// Mathematical left flattened parenthesis
#let lgroup = symbol("\u{27EE}")

/// Less common ones

// Left white curly bracket
#let lBrace = symbol("\u{2983}")
// Left white parenthesis
#let lParen = symbol("\u{2985}")
// Z notation left image bracket
#let llparenthesis = symbol("\u{2987}")
// Z notation left binding bracket
#let llangle = symbol("\u{2989}")
// Left square bracket with underbar
#let lbrakubar = symbol("\u{298B}")
// Left square bracket with tick in top corner
#let lbrackultick = symbol("\u{298D}")
// Left square bracket with tick in bottom corner
#let lbracklltick = symbol("\u{298F}")
// Left angle bracket with dot
#let langledot = symbol("\u{2991}")
// Left arc less-than bracket
#let lparengtr = symbol("\u{2993}")
// Double left arc greater-than bracket
#let Lparenless = symbol("\u{2995}")
// Left black tortoise shell bracket
#let lblkbrbrak = symbol("\u{2997}")
// Left wiggly fence
#let lvzigzag = symbol("\u{29D8}")
// Left double wiggly fence
#let Lvzigzag = symbol("\u{29DA}")
// Left pointing curved angle bracket
#let lcurvyangle = symbol("\u{29FC}")

// Closing symbols (mathclose)

// Exclamation mark
#let mathexclam = symbol("\u{0021}" )
// Right parenthesis
#let rparen = symbol("\u{0029}")
// Right square bracket
#let rbrack = symbol("\u{005D}")
// Right curly bracket
#let rbrace = symbol("\u{007D}")
// Right ceiling
#let rceil = symbol("\u{2309}")
// Right floor
#let rfloor = symbol("\u{230B}")
// Upper-right corner
#let urcorner = symbol("\u{231D}")
// Lower-right corner
#let lrcorner = symbol("\u{231F}")
// Upper right or lower left curly bracket section
#let rmoustache = symbol("\u{23B1}")
// Light right tortoise shell bracket ornament
#let rbrbrak = symbol("\u{2773}")
// Right S-shaped bag delimiter
#let rbag = symbol("\u{27C6}")
// Mathematical right white square bracket
#let rBrack = symbol("\u{27E7}")
// Mathematical right angle bracket
#let rangle = symbol("\u{27E9}")
// Mathematical right double angle bracket
#let rAngle = symbol("\u{27EB}")
// Mathematical right white tortoise shell bracket
#let Rbrbrak = symbol("\u{27ED}")
// Mathematical right flattened parenthesis
#let rgroup = symbol("\u{27EF}")
// Right white curly bracket
#let rBrace = symbol("\u{2984}")
// Right white parenthesis
#let rParen = symbol("\u{2986}")
// Z notation right image bracket
#let rrparenthesis = symbol("\u{2988}")
// Z notation right binding bracket
#let rrangle = symbol("\u{298A}")
// Right square bracket with underbar
#let rbrakubar = symbol("\u{298C}")
// Right square bracket with tick in bottom corner
#let rbracklrtick = symbol("\u{298E}")
// Right square bracket with tick in top corner
#let rbrackurtick = symbol("\u{2990}")
// Right angle bracket with dot
#let rangledot = symbol("\u{2992}")
// Right arc less-than bracket
#let rparengtr = symbol("\u{2994}")
// Double right arc greater-than bracket
#let Rparenless = symbol("\u{2996}")
// Right black tortoise shell bracket
#let rblkbrbrak = symbol("\u{2998}")
// Right wiggly fence
#let rvzigzag = symbol("\u{29D9}")
// Right double wiggly fence
#let Rvzigzag = symbol("\u{29DB}")
// Right pointing curved angle bracket
#let rcurvyangle = symbol("\u{29FD}")

// LR Pairs

// Delimited parentheses
#let paren(arg) = { math.lr([#lparen #arg #rparen]) }
// Delimited square brackets
#let brack(arg) = { math.lr([#lbrack #arg #rbrack]) }
// Delimited curly braces
#let brace(arg) = { math.lr([#lbrace #arg #rbrace]) }
#let Set = brace
// Delimited ceiling
#let ceil(arg) = { math.lr([#lceil #arg #rceil]) }
// Delimited floor
#let floor(arg) = { math.lr([#lfloor #arg #rfloor]) }
// Delimited upper-left and lower-right corners
#let ucorner(arg) = { math.lr([#ulcorner #arg #urcorner]) }
// Delimited lower-left and upper-right corners
#let lcorner(arg) = { math.lr([#llcorner #arg #lrcorner]) }
// Delimited moustaches
#let moustache(arg) = { math.lr([#lmoustache #arg #rmoustache]) }
// Delimited tortoise shell brackets
#let brbrak(arg) = { math.lr([#lbrbrak #arg #rbrbrak]) }
#let tortoise = brbrak
// Delimited S-shaped bags
#let bag(arg) = { math.lr([#lbag #arg #rbag]) }
// Delimited white square brackets
#let Brack(arg) = { math.lr([#lBrack #arg #rBrack]) }
// Delimited angle brackets
#let angle(arg) = { math.lr([#langle #arg #rangle]) }

#let ang = symbol("\u{2220}")
// Delimited double angle brackets
#let Angle(arg) = { math.lr([#lAngle #arg #rAngle]) }
// Delimited white tortoise shell brackets
#let Brbrack(arg) = { math.lr([#Lbrbrak #arg #Rbrbrak]) }
#let Tortoise(arg) = Brbrack
// Delimited flattened parentheses
#let group(arg) = { math.lr([#lgroup #arg #rgroup]) }
// Delimited white curly braces
#let Brace(arg) = { math.lr([#lBrace #arg #rBrace]) }
// Delimited white parentheses
#let Paren(arg) = { math.lr([#lParen #arg #rParen]) }
// Delimited Z notation image brackets
#let Parenthesis(arg) = { math.lr([#llparenthesis #arg #rrparenthesis]) }
// Delimited Z notation angle brackets
#let aangle(arg) = { math.lr([#llangle #arg #rrangle]) }
// Delimited square brackets with underbar
#let brackubar(arg) = { math.lr([#lbrakubar #arg #rbrakubar]) }
// Delimited square brackets with ticks in bottom corners
#let brackltick(arg) = { math.lr([#lbracklltick #arg #rbracklrtick]) }
// Delimited square brackets with ticks in top corners
#let brackutick(arg) = { math.lr([#lbrackultick #arg #rbrackurtick]) }
// Delimited angle brackets with a dot
#let angledot(arg) = { math.lr([#langledot #arg #rangledot]) }
// Delimited arc less-than brackets
#let parengt(arg) = { math.lr([#lparengtr #arg #rparengtr]) }
#let parengtr = parengt
// Delimited double arc greater-than brackets
#let parenlt(arg) = { math.lr([#Lparenless #arg #Rparenless]) }
#let Parenless = parenlt
// Delimited black tortoise shell brackets
#let blkbrbrak(arg) = { math.lr([#lblkbrbrak #arg #rblkbrbrak]) }
#let blacktortoise = blkbrbrak
// Delimited wiggly fences
#let zigzag(arg) = { math.lr([#lvzigzag #arg #rvzigzag]) }
// Delimited double wiggly fences
#let Zigzag(arg) = { math.lr([#Lvzigzag #arg #Rvzigzag]) }
// Delimited curved angle brackets
#let curvyangle(arg) = { math.lr([#lcurvyangle #arg #rcurvyangle]) }

// Fences
// Vertical bar, fence symbol
#let vert = symbol(
  "\u{007C}",
  ("double", "\u{2016}"),
  ("triple", "\u{2AEE}"),
)
// Double vertical bar, fence symbol
#let Vert = symbol("\u{2016}")
// Triple vertical bar delimiter, fence symbol
#let Vvert = symbol("\u{2AEE}")

// Punctuations (mathpunct)
#let mathpunct(it) = {
  math.class("punctuation", symbol(it))
 }
#let punct = symbol(
  ("comma", "\u{002C}"),
  ("colon", "\u{003A}"),
  ("semicolon", "\u{003B}"),
)
// Comma, punctuation symbol
#let mathcomma = mathpunct("\u{002C}")
// Colon, punctuation symbol
#let mathcolon = mathpunct("\u{003A}")
// Semicolon, punctuation symbol
#let mathsemicolon = mathpunct("\u{003B}")

// Over symbols

// Top square bracket
#let overbracket(arg) = { math.accent([#arg], "\u{23B4}") }
// Top parenthesis for mathematical use. Not to be confused with inverted breve (U+0311).
#let overparen(arg) = { math.accent([#arg], "\u{23DC}") }
// Top curly bracket
#let overbrace(arg) = { math.accent([#arg], "\u{23DE}") }

// Under symbols

// Bottom square bracket
#let underbracket(arg) = { math.accent([#arg], "\u{23B5}") }
// Bottom parenthesis for mathematical use.
#let underparen(arg) = { math.accent([#arg], "\u{23DD}") }
// Bottom curly bracket
#let underbrace(arg) = { math.accent([#arg], "\u{23DF}") }

// Math accents

// Hat accent used in maths. Not to be confused with the text circumflex.
#let hat(arg) = { math.accent([#arg], "\u{0302}") }
#let macron(arg) = { math.accent([#arg], "\u{0304}") }
#let bar(arg) = { math.accent([#arg], "\u{0305}") }
#let check(arg) = { math.accent([#arg], "\u{030C}") }
#let hacek = check
#let ddot(arg) = { math.accent([#arg], "\u{0308}") }
#let hook(arg) = { math.accent([#arg], "\u{0309}") }
#let ovhook = hook
#let ring(arg) = { math.accent([#arg], "\u{030A}") }
#let ocirc = ring
#let candra(arg) = { math.accent([#arg], "\u{0310}") }
#let turnedcomma(arg) = { math.accent([#arg], "\u{0312}") }
#let droang(arg) = { math.accent([#arg], "\u{31A}") }
#let leftharpoon(arg) = { math.accent([#arg], "\u{20D0}") }
#let rightharpoon(arg) = { math.accent([#arg], "\u{20D1}") }
#let vertoverlay(arg) = { math.accent([#arg], "\u{20D2}") }
#let overrightarrow(arg) = { math.accent([#arg], "\u{20D7}") }
#let dddot(arg) = { math.accent([#arg], "\u{20DB}") }
#let ddddot(arg) = { math.accent([#arg], "\u{20DC}") }
#let annuity(arg) = { math.accent([#arg], "\u{20E7}") }
#let asterisk(arg) = { math.accent([#arg], "\u{20F0}") }

// bottom accents
#let underbar(arg) = { math.accent([#arg], "\u{0332}") }
#let underdddot(arg) = { math.accent([#arg], "\u{20E8}") }


// Some operators
/// big symbols

// Double-struck N-ary summation operator
#let Bbbsum = symbol("\u{2140}")
// Product operator
#let prod = symbol("\u{220F}")
// Co-product operator
#let coprod = symbol("\u{2210}")
#let bigcup = symbol("\u{22C3}")
#let bigcupdot = math.equation(
  [$bigcup negthinmuskip dot$],
)

/// integrals (see also: integral)
#let int = symbol(
  "\u{222b}",
  ("cw", "\u{2231}"),
  ("ccw", "\u{2A11}"),
  ("f", "\u{2A0F}"),
  ("bar", "\u{2A0D}"),
  ("Bar", "\u{2A0E}"),
  ("rppol", "\u{2A12}"),
  ("scpol", "\u{2A13}"),
  ("npol", "\u{2A14}"),
  ("point", "\u{2A15}"),
  ("sq", "\u{2A16}"),
  ("larhk", "\u{2A17}"),
  ("x", "\u{2A18}"),
  ("times", "\u{2A18}"),
  ("cap", "\u{2A19}"),
  ("cup", "\u{2A1A}"),
  ("up", "\u{2A1B}"),
)
#let intclockwise = math.equation([$ int.cw $])
#let oint = symbol(
  "\u{222e}",
  ("cw", "\u{2232}"),
  ("ccw", "\u{2233}"),
)
#let ointclockwise = math.equation([$oint.cw$])
#let ointcounterclockwise = math.equation([$oint.ccw$])

#let iint = math.equation([$integral.double$])
#let oiint = symbol("\u{222f}") // integral.surf
#let iiint = math.equation([$integral.triple$])
#let oiiint = symbol("\u{2230}") // integral.vol

#let idotsint = math.equation([$integral negthinmuskip ... negthinmuskip integral$])

#let bigwedge = symbol("\u{22C0}")
#let bigvee = symbol("\u{22C1}")
#let bigcap = symbol("\u{22C2}")
#let bigcup = symbol("\u{22C3}")
#let leftouterjoin = symbol("\u{27D5}")
#let rightouterjoin = symbol("\u{27D6}")
#let fullouterjoin = symbol("\u{27D7}")
#let bigbot = symbol("\u{27D8}")
#let bigtop = symbol("\u{27D9}")
#let bigsolidus = symbol(
  "\u{29F8}",
  ("reverse", "\u{29F9}"),
)
#let bigodot = symbol("\u{2A00}")
#let bigoplus = symbol("\u{2A01}")
#let bigotimes = symbol("\u{2A02}")
#let bigcupdot = symbol("\u{2A03}")
#let biguplus = symbol("\u{2A04}")
#let bigsqcap = symbol("\u{2A05}")
#let bigsqcup = symbol("\u{2A06}")
#let conjquant = symbol("\u{2A07}")
#let disjquant = symbol("\u{2A08}")
#let bigtimes = symbol("\u{2A09}")
#let modtwosum = symbol("\u{2A0A}") //
// sum.integral
#let sumint = symbol("\u{2A0B}")
// integral.quad
#let iiiint = symbol("\u{2A0C}")
// integral.dash
#let intbar = symbol("\u{2A0D}")
// integral.dash.double
#let intBar = symbol("\u{2A0E}")
// integral.slash
#let fint = symbol("\u{2A0F}")
// ---
#let cirfnint = symbol("\u{2A10}")
// integral.ccw
#let awint = symbol("\u{2A11}")
#let rppolint = symbol("\u{2A12}") // ---
#let scpolint = symbol("\u{2A13}") // ---
#let npolint = symbol("\u{2A14}") // ---
#let pointint = symbol("\u{2A15}") // ---
// integral.square
#let sqint = symbol("\u{2A16}")
// integral.arrow.hook
#let intlarhk = symbol("\u{2A17}")
// integral.times
#let intx = symbol("\u{2A18}")
// integral.inter
#let intcap = symbol("\u{2A19}")
// integral.union
#let intcup = symbol("\u{2A1A}")
#let upint = symbol("\u{2A1B}")
#let lowint = symbol("\u{2A1C}")
#let join = symbol("\u{2A1D}")
#let bigtriangleleft = symbol("\u{2A1E}")

// z notations

#let zcmp = symbol("\u{2A1F}")
#let zpipe = symbol("\u{2A20}")
#let zproject = symbol("\u{2A21}")
// interleave.big
#let biginterleave = symbol("\u{2AFC}")
#let bigtallobolong = symbol("\u{2AFF}")
#let arabicmaj = symbol("\u{1EEF0}")
#let arabichad = symbol("\u{1EEF1}")

// Mathbins


#let mathbin(it) = {
  math.class("binary", symbol(it))
}
// +, plus sign
#let plus = mathbin("\u{002B}")
// -, minus sign
#let minus = mathbin("\u{2212}")
// +-, plus-or-minus sign
#let pm = mathbin("\u{00B1}")
// dot.c, centerdot, middle dot
#let cdot = mathbin("\u{00B7}")
// ×, multiply sign
#let times = mathbin("\u{00D7}")
// ÷, division sign
#let div = mathbin("\u{00F7}")
// dagger relation, Typst sets it as mathrel for some reason. See also: https://github.com/latex3/unicode-math/issues/619
#let dagger = mathbin("\u{2020}")
// double dagger relation, Typst sets it as mathrel for some reason. See also: https://github.com/latex3/unicode-math/issues/619
#let ddagger = mathbin("\u{2021}")
// round bullet, filled
#let smlbkcircle = mathbin("\u{2022}")
// character tie, z notation sequence concatenation
#let tieconcat = mathbin("\u{2040}")
// turned ampersand
#let upand = mathbin("\u{214B}")
// plus sign, dot above
#let dotplus = mathbin("\u{2214}")
// division slash
#let divslash = mathbin("\u{2215}")
// set minus (as opposed to a revserse solidus)
#let setminus = mathbin("\u{2216}")


/// Relational operators
#let mathrel(it) = {
  math.class("relation", symbol(it))
}
// amalgam
#let amalg = mathrel("\u{2A3F}")


// Ordinary symbols
#let mathord(it) = {
  math.class("normal", symbol(it))
}

#let sign = symbol(
  ("hash", "\u{23}"),
  ("dollar", "\u{24}"),
  ("percent", "\u{25}"),
  ("ampersand", "\u{26}"),
  ("period", "\u{2E}"),
  ("fullstop", "\u{2E}"),
  ("slash", "\u{2F}"),
  ("question", "\u{3F}"),
  ("at", "\u{40}"),
  ("backslash", "\u{5C}"),
  ("reversesolidus", "\u{5C}"),
  ("sterling", "\u{A3}"),
  ("pound", "\u{A3}"),
  ("yen", "\u{A5}"),
  ("section", "\u{A7}"),
  ("neg", "\u{AC}"),
  ("paragraph", "\u{B6}"),
  ("zbar", "\u{1B5}"),
  ("euro", "\u{20AC}"),
)

#let mathoctothorpe = mathord("\u{0023}")
#let hash = mathoctothorpe
#let mathdollar = mathord("\u{0024}")
#let mathpercent = mathord("\u{0025}")
#let mathampersand = mathord("\u{0026}")
#let mathperiod = mathord("\u{002E}")
#let mathslash = mathord("\u{002F}")
#let mathquestion = mathord("\u{003F}")
#let mathat = mathord("\u{0040}")
#let mathatsign = mathat
#let mathbackslash = mathord("\u{005C}")
#let mathsterling = mathord("\u{00A3}")
#let mathpound = mathsterling
#let mathyen = mathord("\u{00A5}")
#let mathsection = mathord("\u{00A7}")
#let neg = mathord("\u{00AC}")
#let mathparagraph = mathord("\u{00B6}")
#let zbar = mathord("\u{1B5}")

#let upbackepsilon = mathord("\u{3F6}")
#let horizbar = mathord("\u{2015}")
#let twolowline = mathord("\u{2017}")
#let enleadertwodots = mathord("\u{2025}")
#let unicodeellipsis = mathord("\u{2026}")
#let ellipsis = unicodeellipsis
#let prime = symbol(
  "\u{2032}",
  ("double", "\u{2033}"),
  ("triple", "\u{2034}"),
  ("quadruple", "\u{2057}"),
  ("back", "\u{2035}"),
  ("backdouble", "\u{2036}"),
  ("backtriple", "\u{2037}"),
)
#let dprime = mathord("\u{2033}")
#let trprime = mathord("\u{2034}")
#let qprime = mathord("\u{2057}")
#let backprime = mathord("\u{2035}")
#let backdprime = mathord("\u{2036}")
#let backtrprime = mathord("\u{2037}")
#let caretinsert = mathord("\u{2038}")
#let Exclam = mathord("\u{203C}")
#let hyphenbullet = mathord("\u{2043}")
#let Question = mathord("\u{2047}")

#let enclose = symbol(
  ("circle", "\u{20DD}"),
  ("square", "\u{20DE}"),
  ("diamond", "\u{20DF}"),
  ("triangle", "\u{20E4}"),
)
#let enclosecircle = enclose.circle
#let enclosesquare = enclose.square
#let enclosediamond = enclose.diamond
#let enclosetriangle = enclose.triangle

// Euler constant
#let Eulerconst = mathord("\u{2107}")
// Plank constant
#let Plankconst = mathord("\u{210F}")
// Conductance
#let mho = mathord("\u{2127}")
// Turned capital F
#let Finv = mathord("\u{2132}")
// Double-struct small pi
#let Bbbpi = mathord("\u{213C}")
// Turned sans-serif capital G
#let Game = mathord("\u{2141}")
// Turned sans-serif capital L
#let sansLturned = mathord("\u{2142}")
// Reversed sans-serif capital L
#let sansLmirrored = mathord("\u{2143}")
// Turned sans-serif capital Y
#let Yup = mathord("\u{2144}")

// Double strucks

// Double-struct italic capital D
#let mitBbbD = mathord("\u{2145}")
// Double-struct italic small D
#let mitBbbd = mathord("\u{2146}")
// Double-struct italic small E
#let mitBbbe = mathord("\u{2147}")
// Double-struct italic small i
#let mitBbbi = mathord("\u{2148}")
// Double-struct italic small j
#let mitBbbj = mathord("\u{2149}")

// Property line
#let Propertyline = mathord("\u{214A}")
// Up-down arrow with perpendicular base
#let updownarrowbar = mathord("\u{21A8}")
// Rightwards arrows with corner downwards; also called line feed (LF)
#let linefeed = mathord("\u{21B4}")
#let LF = linefeed
// Downwards arrow with corner leftward; also called carriage return (CR)
#let carriagereturn = mathord("\u{21B5}")
#let CR = carriagereturn

// North-west arrow to long bar
#let barovernorthwestarrow = mathord("\u{21B8}")
// Leftwards arrow to bar over rightwards arrow to bar
#let barleftarrowrightarrowbar = mathord("\u{21B9}")
// Anticlockwise open circle arrow
#let acwopencirclearrow = mathord("\u{21BA}")
// Clockwise open circle arrow
#let cwopencirclearrow = mathord("\u{21BB}")
// Upwards arrow with double stroke
#let nHuparrow = mathord("\u{21DE}")
// Downwards arrow with double stroke
#let nHdownarrow = mathord("\u{21DF}")
// Leftwards dash arrow
#let leftdasharrow = mathord("\u{21E0}")
// Rightwards dash arrow
#let rightdasharrow = mathord("\u{21E2}")
// Upwards dash arrow
#let updasharrow = mathord("\u{21E1}")
// Downwards dash arrow
#let downdasharrow = mathord("\u{21E3}")