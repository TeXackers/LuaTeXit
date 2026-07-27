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

// amalgam
#let amalg = mathbin("\u{2A3F}")


/// Relational operators
#let mathrel(it) = {
  math.class("relation", symbol(it))
}
// less-than sign
#let less = mathrel("\u{003C}")
// equals sign
#let equal = mathrel("\u{003D}")
// greater-than sign
#let greater = mathrel("\u{003E}")
// close up
#let closure = mathrel("\u{2050}")
// leftward arrow
#let leftarrow = mathrel("\u{2190}")
// upward arrow
#let uparrow = mathrel("\u{2191}")
// rightward arrow
#let rightarrow = mathrel("\u{2192}")
// downward arrow
#let downarrow = mathrel("\u{2193}")
// left and right arrow
#let leftrightarrow = mathrel("\u{2194}")
// up and down arrow
#let updownarrow = mathrel("\u{2195}")
// nw pointing arrow
#let nwarrow = mathrel("\u{2196}")
// ne pointing arrow
#let nearrow = mathrel("\u{2197}")
// se pointing arrow
#let searrow = mathrel("\u{2198}")
// sw pointing arrow
#let swarrow = mathrel("\u{2199}")
// not left arrow
#let nleftarrow = mathrel("\u{219A}")
// not right arrow
#let nrightarrow = mathrel("\u{219B}")
// left arrow-wavy
#let leftwavearrow = mathrel("\u{219C}")
// right arrow-wavy
#let rightwavearrow = mathrel("\u{219D}")
// left two-headed arrow
#let twoheadleftarrow = mathrel("\u{219E}")
// up two-headed arrow
#let twoheaduparrow = mathrel("\u{219F}")
// right two-headed arrow
#let twoheadrightarrow = mathrel("\u{21A0}")
// down two-headed arrow
#let twoheaddownarrow = mathrel("\u{21A1}")
// left arrow-tailed
#let leftarrowtail = mathrel("\u{21A2}")
// right arrow-tailed
#let rightarrowtail = mathrel("\u{21A3}")
// maps to, leftward
#let mapsfrom = mathrel("\u{21A4}")
// maps to, upward
#let mapsto = mathrel("\u{21A5}")
// maps to, rightward
#let mapsto = mathrel("\u{21A6}")
// maps to, downward
#let mapsdown = mathrel("\u{21A7}")
// left arrow-hooked
#let hookleftarrow = mathrel("\u{21A9}")
// right arrow-hooked
#let hookrightarrow = mathrel("\u{21AA}")
// left arrow-looped
#let looparrowleft = mathrel("\u{21AB}")
// right arrow-looped
#let looparrowright = mathrel("\u{21AC}")
// left and right arr-wavy
#let leftrightsquigarrow = mathrel("\u{21AD}")
// not left and right arrow
#let nleftrightarrow = mathrel("\u{21AE}")
// downzigzagarrow
#let downzigzagarrow = mathrel("\u{21AF}")

// lsh a
#let Lsh = mathrel("\u{21B0}")
// rsh a;
#let Rsh = mathrel("\u{21B1}")
// left down angled arrow
#let Ldsh = mathrel("\u{21B2}")
// right down angled arrow
#let Rdsh = mathrel("\u{21B3}")
// left curved arrow
#let curvearrowleft = mathrel("\u{21B6}")
// right curved arrow
#let curvearrowright = mathrel("\u{21B7}")
// left harpoon-up
#let leftharpoonup = mathrel("\u{21BC}")
// left harpoon-down
#let leftharpoondown = mathrel("\u{21BD}")
// up harpoon-right
#let upharpoonright = mathrel("\u{21BE}")
// up harpoon-left
#let upharpoonleft = mathrel("\u{21BF}")


/// Sets
/// Can't define `in` because it's immutable!!
///
// negated set membership
#let notin = mathrel("\u{2209}")
// set membership (Small set)
#let smallin = mathrel("\u{220A}")
// contains, variant
#let ni = mathrel("\u{220B}")
// negated contains, variant
#let nni = mathrel("\u{220C}")
// contains (small)
#let smallni = mathrel("\u{220D}")
// proportional to
#let propto = mathrel("\u{221D}")
// mid
#let mid = mathrel("\u{2223}")
// negated mid
#let nmid = mathrel("\u{2224}")
// parallel
#let parallel = mathrel("\u{2225}")
// not parallel
#let nparallel = mathrel("\u{2226}")
// ratio
#let ratio = mathrel("\u{2236}")
#let mathrio = ratio
// two colons
#let Colon = mathrel("\u{2237}")
// excess
#let dashcolon = mathrel("\u{2239}")
// minus with four dots, geometric properties
#let dotsminusdots = mathrel("\u{223A}")
// homothetic kernel contraction
#let kernelcontraction = mathrel("\u{223B}")
// similar to
#let sim = mathrel("\u{223C}")
// reverse similar
#let backsim = mathrel("\u{223D}")
// not similar to
#let nsim = mathrel("\u{2241}")
// equals, similar
#let eqsim = mathrel("\u{2242}")
// similar, equals
#let simeq = mathrel("\u{2243}")
// not similar, equals
#let nsimeq = mathrel("\u{2244}")
// similar, equals (alias)
#let sime = simeq
#let nsime = nsimeq
// congruent with
#let cong = mathrel("\u{2245}")
// similar, not equals (vert only for 9573 entity)
#let simneqq = mathrel("\u{2246}")
// not congruent with
#let ncong = mathrel("\u{2247}")

// approximately
#let approx = mathrel("\u{2248}")
// not approximately
#let napprox = mathrel("\u{2249}")
// approximate equals
#let approxeq = mathrel("\u{224A}")
// approximate identical to
#let approxident = mathrel("\u{224B}")
// asymptotically equal to
#let asymp = mathrel("\u{224D}")
// bumpy equals
#let Bumpeq = mathrel("\u{224E}")
// bumpy equals, equals
#let bumpeq = mathrel("\u{224F}")
// equals, single dot above
#let doteq = mathrel("\u{2250}")
// equals, even dot above and below
#let Doteq = mathrel("\u{2251}")
// equals, falling dots
#let fallingdotseq = mathrel("\u{2252}")
// equals, rising dots
#let risingdotseq = mathrel("\u{2253}")
// colon, equals
#let coloneq = mathrel("\u{2254}")
// equals, colon
#let eqcolon = mathrel("\u{2255}")
// circle on equals sign
#let eqcirc = mathrel("\u{2256}")
// circle, equals
#let circeq = mathrel("\u{2257}")
// arc, equals; corresponds to
#let arceq = mathrel("\u{2258}")
// corresponds to, wedge/equals
#let wedgeq = mathrel("\u{2259}")
// logical or, equals
#let veeeq = mathrel("\u{225A}")
// star equals
#let stareq = mathrel("\u{225B}")
// triangle, equals
#let triangleq = mathrel("\u{225C}")
// equals by definition
#let eqdef = mathrel("\u{225D}")
// measured by (m over equals)
#let measeq = mathrel("\u{225E}")
// equals with question mark
#let questeq = mathrel("\u{225F}")
// not equal
#let ne = mathrel("\u{2260}")
#let neq = ne

// identical with
#let equiv = mathrel("\u{2261}")
// not identical with
#let nequiv = mathrel("\u{2262}")
// strict equivalence
#let Equiv = mathrel("\u{2263}")
// less than or equal to 
#let leq = mathrel("\u{2264}")
// greater than or equal to
#let geq = mathrel("\u{2265}")
// less, double equals
#let leqq = mathrel("\u{2266}")
// greater, double equals
#let geqq = mathrel("\u{2267}")
// less, not double equals
#let lneqq = mathrel("\u{2268}")
// greater, not double equals
#let gneqq = mathrel("\u{2269}")
// much less than
#let ll = mathrel("\u{226A}")
// much greater than
#let gg = mathrel("\u{226B}")
// between
#let between = mathrel("\u{226C}")
// not asymptotically equal to
#let nasymp = mathrel("\u{226D}")
// not less than
#let nless = mathrel("\u{226E}")
// not greater than
#let ngtr = mathrel("\u{226F}")
// not less-than-or-equal
#let nleq = mathrel("\u{2270}")
// not greater-than-or-equal
#let ngeq = mathrel("\u{2271}")
// less, similar
#let lesssim = mathrel("\u{2272}")
// greater, similar
#let gtrsim = mathrel("\u{2273}")
// not less, similar
#let nlesssim = mathrel("\u{2274}")
// not greater, similar
#let ngtrsim = mathrel("\u{2275}")
// less greater
#let lessgtr = mathrel("\u{2276}")
#let lg = lessgtr
// greater less
#let gtrless = mathrel("\u{2277}")
#let gl = gtrless
// not less, greater
#let nlessgtr = mathrel("\u{2278}")
// not greater, less
#let ngtrless = mathrel("\u{2279}")

// precedes
#let prec = mathrel("\u{227A}")
// succeeds
#let succ = mathrel("\u{227B}")
// precedes, curly equals
#let preccurlyeq = mathrel("\u{227C}")
// succeeds, curly equals
#let succcurlyeq = mathrel("\u{227D}")
// precedes, similar
#let precsim = mathrel("\u{227E}")
// succeeds, similar
#let succsim = mathrel("\u{227F}")
// not precedes
#let nprec = mathrel("\u{2280}")
// not succeeds
#let nsucc = mathrel("\u{2281}")

// subset or is implied by
#let subset = mathrel("\u{2282}")
// superset or implies
#let supset = mathrel("\u{2283}")
// 

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



#let mathalpha(it) = {
  math.class("normal", symbol(it))
}

/// Normal weight
/// Upright Greek
#let mathup = symbol(
  ("Alpha", "\u{0391}"),
  ("Beta", "\u{0392}"),
  ("Gamma", "\u{0393}"),
  ("Delta", "\u{0394}"),
  ("Epsilon", "\u{0395}"),
  ("Zeta", "\u{0396}"),
  ("Eta", "\u{0397}"),
  ("Theta", "\u{0398}"),
  ("Iota", "\u{0399}"),
  ("Kappa", "\u{039A}"),
  ("Lambda", "\u{039B}"),
  ("Mu", "\u{039C}"),
  ("Nu", "\u{039D}"),
  ("Xi", "\u{039E}"),
  ("Omicron", "\u{039F}"),
  ("Pi", "\u{03A0}"),
  ("Rho", "\u{03A1}"),
  ("Sigma", "\u{03A3}"),
  ("Tau", "\u{03A4}"),
  ("Upsilon", "\u{03A5}"),
  ("Phi", "\u{03A6}"),
  ("Chi", "\u{03A7}"),
  ("Psi", "\u{03A8}"),
  ("Omega", "\u{03A9}"),
  ("varTheta", "\u{03F4}"),
  // lowercase
  ("alpha", "\u{03B1}"),
  ("beta", "\u{03B2}"),
  ("gamma", "\u{03B3}"),
  ("delta", "\u{03B4}"),
  ("epsilon", "\u{03B5}"),
  ("zeta", "\u{03B6}"),
  ("eta", "\u{03B7}"),
  ("theta", "\u{03B8}"),
  ("iota", "\u{03B9}"),
  ("kappa", "\u{03BA}"),
  ("lambda", "\u{03BB}"),
  ("mu", "\u{03BC}"),
  ("nu", "\u{03BD}"),
  ("xi", "\u{03BE}"),
  ("omicron", "\u{03BF}"),
  ("pi", "\u{03C0}"),
  ("rho", "\u{03C1}"),
  ("sigma", "\u{03C2}"),
  ("tau", "\u{03C3}"),
  ("upsilon", "\u{03C4}"),
  ("phi", "\u{03C5}"),
  ("chi", "\u{03C6}"),
  ("psi", "\u{03C7}"),
  ("omega", "\u{03C8}"),
  ("varepsilon", "\u{03F5}"),
  ("vartheta", "\u{03D1}"),
  ("varpi", "\u{03D6}"),
  ("varkappa", "\u{03F0}"),
  ("varrho", "\u{03F1}"),
  ("varsigma", "\u{03C2}"),
  ("varphi", "\u{03C6}"),
  // less common ones
  ("Digamma", "\u{03DC}"),
  ("digamma", "\u{03DD}"),
)



/// Italic
#let mathit = symbol(
  // Latin
  ("A", "\u{1D434}"),
  ("B", "\u{1D435}"),
  ("C", "\u{1D436}"),
  ("D", "\u{1D437}"),
  ("E", "\u{1D438}"),
  ("F", "\u{1D439}"),
  ("G", "\u{1D43A}"),
  ("H", "\u{1D43B}"),
  ("I", "\u{1D43C}"),
  ("J", "\u{1D43D}"),
  ("K", "\u{1D43E}"),
  ("L", "\u{1D43F}"),
  ("M", "\u{1D440}"),
  ("N", "\u{1D441}"),
  ("O", "\u{1D442}"),
  ("P", "\u{1D443}"),
  ("Q", "\u{1D444}"),
  ("R", "\u{1D445}"),
  ("S", "\u{1D446}"),
  ("T", "\u{1D447}"),
  ("U", "\u{1D448}"),
  ("V", "\u{1D449}"),
  ("W", "\u{1D44A}"),
  ("X", "\u{1D44B}"),
  ("Y", "\u{1D44C}"),
  ("Z", "\u{1D44D}"),
  ("a", "\u{1D44E}"),
  ("b", "\u{1D44F}"),
  ("c", "\u{1D450}"),
  ("d", "\u{1D451}"),
  ("e", "\u{1D452}"),
  ("f", "\u{1D453}"),
  ("g", "\u{1D454}"),
  ("h", "\u{1D455}"),
  ("i", "\u{1D456}"),
  ("j", "\u{1D457}"),
  ("k", "\u{1D458}"),
  ("l", "\u{1D459}"),
  ("m", "\u{1D45A}"),
  ("n", "\u{1D45B}"),
  ("o", "\u{1D45C}"),
  ("p", "\u{1D45D}"),
  ("q", "\u{1D45E}"),
  ("r", "\u{1D45F}"),
  ("s", "\u{1D460}"),
  ("t", "\u{1D461}"),
  ("u", "\u{1D462}"),
  ("v", "\u{1D463}"),
  ("w", "\u{1D464}"),
  ("x", "\u{1D465}"),
  ("y", "\u{1D466}"),
  ("z", "\u{1D467}"),
  // Greek
  ("Alpha", "\u{1D6E2}"),
  ("Beta", "\u{1D6E3}"),
  ("Gamma", "\u{1D6E4}"),
  ("Delta", "\u{1D6E5}"),
  ("Epsilon", "\u{1D6E6}"),
  ("Zeta", "\u{1D6E7}"),
  ("Eta", "\u{1D6E8}"),
  ("Theta", "\u{1D6E9}"),
  ("Iota", "\u{1D6EA}"),
  ("Kappa", "\u{1D6EB}"),
  ("Lambda", "\u{1D6EC}"),
  ("Mu", "\u{1D6ED}"),
  ("Nu", "\u{1D6EE}"),
  ("Xi", "\u{1D6EF}"),
  ("Omicron", "\u{1D6F0}"),
  ("Pi", "\u{1D6F1}"),
  ("Rho", "\u{1D6F2}"),
  ("varTheta", "\u{1D6F3}"),
  ("Sigma", "\u{1D6F4}"),
  ("Tau", "\u{1D6F5}"),
  ("Upsilon", "\u{1D6F6}"),
  ("Phi", "\u{1D6F7}"),
  ("Chi", "\u{1D6F8}"),
  ("Psi", "\u{1D6F9}"),
  ("Omega", "\u{1D6FA}"),
  // greek lowercase
  ("alpha", "\u{1D6FC}"),
  ("beta", "\u{1D6FD}"),
  ("gamma", "\u{1D6FE}"),
  ("delta", "\u{1D6FF}"),
  ("varepsilon", "\u{1D700}"),
  ("zeta", "\u{1D701}"),
  ("eta", "\u{1D702}"),
  ("theta", "\u{1D703}"),
  ("iota", "\u{1D704}"),
  ("kappa", "\u{1D705}"),
  ("lambda", "\u{1D706}"),
  ("mu", "\u{1D707}"),
  ("nu", "\u{1D708}"),
  ("xi", "\u{1D709}"),
  ("omicron", "\u{1D70A}"),
  ("pi", "\u{1D70B}"),
  ("rho", "\u{1D70C}"),
  ("varsigma", "\u{1D70D}"),
  ("sigma", "\u{1D70E}"),
  ("tau", "\u{1D70F}"),
  ("upsilon", "\u{1D710}"),
  ("phi", "\u{1D711}"),
  ("chi", "\u{1D712}"),
  ("psi", "\u{1D713}"),
  ("omega", "\u{1D714}"),
  // less known ones
  ("partial", "\u{1D715}"),
  ("epsilon", "\u{1D716}"),
  ("vartheta", "\u{1D717}"),
  ("varkappa", "\u{1D718}"),
  ("varphi", "\u{1D719}"),
  ("varpi", "\u{1D71A}")
)