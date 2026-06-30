from discord import Colour


class GithubColour(Colour):
    """
    Class for Github Brand Colours.

    As per Github, the palettes are divy'd up into three sub-categories:
    - Primary: Colours that represent the brand, and are used in the logo and other key brand assets.
    - Copilot: Colours that represent the Github Copilot product, and are used in the Copilot logo and other key Copilot brand assets.
    - Security: Colours that represent the Github Security product, and are used in the Security logo and other key Security brand assets.

    ## How to use
    GithubColour.primary.green1
    GithubColour.copilot.purple3
    GithubColour.security.blue2
    """

    github_green: Colour = Colour.from_rgb(15, 191, 62)
    """RGB(15, 191, 62)"""
    copilot_purple: Colour = Colour.from_rgb(133, 52, 243)
    """RGB(133, 52, 243)"""
    security_blue: Colour = Colour.from_rgb(48, 148, 255)
    """RGB(48, 148, 255)"""

    class primary:
        """
        Primary colours that represent the Github brand.

        Includes grey and green palettes.
        """

        grey1: Colour = Colour.from_rgb(242, 245, 243)
        """RGB(242, 245, 243)"""
        grey2: Colour = Colour.from_rgb(228, 235, 230)
        """RGB(228, 235, 230)"""
        grey3: Colour = Colour.from_rgb(182, 191, 184)
        """RGB(182, 191, 184)"""
        grey4: Colour = Colour.from_rgb(144, 150, 146)
        """RGB(144, 150, 146)"""
        grey5: Colour = Colour.from_rgb(34, 41, 37)
        """RGB(34, 41, 37)"""
        grey6: Colour = Colour.from_rgb(16, 20, 17)
        """RGB(16, 20, 17)"""
        green1: Colour = Colour.from_rgb(191, 255, 209)
        """RGB(191, 255, 209)"""
        green2: Colour = Colour.from_rgb(140, 242, 166)
        """RGB(140, 242, 166)"""
        green3: Colour = Colour.from_rgb(95, 237, 131)
        """RGB(95, 237, 131)"""
        green4: Colour = Colour.from_rgb(15, 191, 62)
        """RGB(15, 191, 62)"""
        green5: Colour = Colour.from_rgb(8, 135, 43)
        """RGB(8, 135, 43)"""
        green6: Colour = Colour.from_rgb(10, 36, 27)
        """RGB(10, 36, 27)"""

    class copilot:
        """
        Colours that represent the Github Copilot product.

        Includes purple and orange palettes.
        """

        purple1: Colour = Colour.from_rgb(200, 152, 253)
        """RGB(200, 152, 253)"""
        purple2: Colour = Colour.from_rgb(184, 112, 255)
        """RGB(184, 112, 255)"""
        purple3: Colour = Colour.from_rgb(133, 52, 243)
        """RGB(133, 52, 243)"""
        purple4: Colour = Colour.from_rgb(67, 23, 158)
        """RGB(67, 23, 158)"""
        purple5: Colour = Colour.from_rgb(38, 17, 95)
        """RGB(38, 17, 95)"""
        purple6: Colour = Colour.from_rgb(22, 0, 72)
        """RGB(22, 0, 72)"""
        orange1: Colour = Colour.from_rgb(244, 168, 118)
        """RGB(244, 168, 118)"""
        orange2: Colour = Colour.from_rgb(240, 138, 58)
        """RGB(240, 138, 58)"""
        orange3: Colour = Colour.from_rgb(254, 76, 37)
        """RGB(254, 76, 37)"""
        orange4: Colour = Colour.from_rgb(197, 50, 17)
        """RGB(197, 50, 17)"""
        orange5: Colour = Colour.from_rgb(128, 30, 15)
        """RGB(128, 30, 15)"""
        orange6: Colour = Colour.from_rgb(80, 10, 0)
        """RGB(80, 10, 0)"""

    class security:
        """
        Colours that represent the Github Security product.

        Includes blue and lime palettes.
        """

        blue1: Colour = Colour.from_rgb(158, 236, 255)
        """RGB(158, 236, 255)"""
        blue2: Colour = Colour.from_rgb(48, 148, 255)
        """RGB(48, 148, 255)"""
        blue3: Colour = Colour.from_rgb(0, 110, 219)
        """RGB(0, 110, 219)"""
        blue4: Colour = Colour.from_rgb(5, 39, 252)
        """RGB(5, 39, 252)"""
        blue5: Colour = Colour.from_rgb(33, 33, 131)
        """RGB(33, 33, 131)"""
        blue6: Colour = Colour.from_rgb(0, 28, 77)
        """RGB(0, 28, 77)"""
        lime1: Colour = Colour.from_rgb(220, 255, 150)
        """RGB(220, 255, 150)"""
        lime2: Colour = Colour.from_rgb(221, 250, 5)
        """RGB(221, 250, 5)"""
        lime3: Colour = Colour.from_rgb(216, 189, 14)
        """RGB(216, 189, 14)"""
        lime4: Colour = Colour.from_rgb(219, 157, 0)
        """RGB(219, 157, 0)"""
        lime5: Colour = Colour.from_rgb(214, 114, 0)
        """RGB(214, 114, 0)"""
        lime6: Colour = Colour.from_rgb(112, 49, 0)
        """RGB(112, 49, 0)"""

    class primitive:
        """
        Primitive colours used by Github Brand, available in CSS and other design tools, but not part of the official brand palette."""

        class fg:
            accent: Colour = Colour.from_str("#0969da")
            """#0969da"""
            attention: Colour = Colour.from_str("#9a6700")
            """#9a6700"""
            black: Colour = Colour.from_str("#1f2328")
            """#1f2328"""
            closed: Colour = Colour.from_str("#d1242f")
            """#d1242f"""
            danger: Colour = Colour.from_str("#d1242f")
            """#d1242f"""
            default: Colour = Colour.from_str("#1f2328")
            """#1f2328"""
            disabled: Colour = Colour.from_str("#818b98")
            """#818b98"""
            done: Colour = Colour.from_str("#8250df")
            """#8250df"""
            draft: Colour = Colour.from_str("#59636e")
            """#59636e"""
            link: Colour = Colour.from_str("#0969da")
            """#0969da"""
            muted: Colour = Colour.from_str("#59636a")
            """#59636a"""
            neutral: Colour = Colour.from_str("#59636a")
            """#59636a"""
            on_emphasis: Colour = Colour.from_str("#ffffff")
            """#ffffff"""
            on_inverse: Colour = Colour.from_str("#ffffff")
            """#ffffff"""
            open: Colour = Colour.from_str("#1a7f37")
            """#1a7f37"""
            severe: Colour = Colour.from_str("#bc4c00")
            """#bc4c00"""
            sponsors: Colour = Colour.from_str("#bf3989")
            """#bf3989"""
            success: Colour = Colour.from_str("#1a7f37")
            """#1a7f37"""
            upsell: Colour = Colour.from_str("#8250df")
            """#8250df"""
            white: Colour = Colour.from_str("#ffffff")
            """#ffffff"""

        class bg:
            class accent:
                emphasis: Colour = Colour.from_str("#0969da")
                """#0969da"""
                muted: Colour = Colour.from_str("#ddf4ff")
                """#ddf4ff"""

            class attention:
                emphasis: Colour = Colour.from_str("#9a6700")
                """#9a6700"""
                muted: Colour = Colour.from_str("#fff8c5")
                """#fff8c5"""

            black: Colour = Colour.from_str("#1f2328")
            """#1f2328"""

            class closed:
                emphasis: Colour = Colour.from_str("#cf222e")
                """#cf222e"""
                muted: Colour = Colour.from_str("#ffebe9")
                """#ffebe9"""

            class danger:
                emphasis: Colour = Colour.from_str("#cf222e")
                """#cf222e"""
                muted: Colour = Colour.from_str("#ffebe9")
                """#ffebe9"""

            default: Colour = Colour.from_str("#ffffff")
            """#ffffff"""
            disabled: Colour = Colour.from_str("#eff2f5")
            """#eff2f5"""

            class done:
                emphasis: Colour = Colour.from_str("#8250df")
                """#8250df"""
                muted: Colour = Colour.from_str("#fbe5ff")
                """#fbe5ff"""

            class draft:
                emphasis: Colour = Colour.from_str("#59636e")
                """#59636e"""
                muted: Colour = Colour.from_str("#818b98")
                """Note: Discord doesn't support true transparency in embed colours, so this is just #818b98 in lieu of #818b981f"""

            emphasis: Colour = Colour.from_str("#25292e")
            """#25292e"""
            inset: Colour = Colour.from_str("#f6f8fa")

            class neutral:
                emphasis: Colour = Colour.from_str("#59636a")
                """#59636a"""
                muted: Colour = Colour.from_str("#818b98")
                """Note: Discord doesn't support true transparency in embed colours, so this is just #818b98 in lieu of #818b981f"""

            class open:  # noqa [A001]
                emphasis: Colour = Colour.from_str("#1a7f37")
                """#1a7f37"""
                muted: Colour = Colour.from_str("#dafbe1")
                """#dafbe1"""

            class severe:
                emphasis: Colour = Colour.from_str("#bc4c00")
                """#bc4c00"""
                muted: Colour = Colour.from_str("#fff1e5")
                """#fff1e5"""

            class sponsors:
                emphasis: Colour = Colour.from_str("#bf3989")
                """#bf3989"""
                muted: Colour = Colour.from_str("#ffeff7")
                """#ffeff7"""

            class success:
                emphasis: Colour = Colour.from_str("#1f883d")
                """#1f883d"""
                muted: Colour = Colour.from_str("#dafbe1")
                """#dafbe1"""

            transparent: Colour = Colour.from_str("#ffffff")
            """Note: Discord doesn't support true transparency in embed colours, so this is just white. #ffffff"""

            class upsell:
                emphasis: Colour = Colour.from_str("#8250df")
                """#8250df"""
                muted: Colour = Colour.from_str("#fbefff")
                """#fbefff"""

            white: Colour = Colour.from_str("#ffffff")
            """#ffffff"""

    class data:
        """
        Colours used in Github data visualisation, such as charts and graphs.

        Includes emphasis/muted variants for the following:
        auburn, blue, brown, coral, grey, green, lemon, lime, olive, orange, pine, pink, plum, purple, red, teal, yellow
        """

        class auburn:
            emphasis: Colour = Colour.from_str("#9d615c")
            """#9d615c"""
            muted: Colour = Colour.from_str("#f2e9e9")
            """#f2e9e9"""

        class blue:
            emphasis: Colour = Colour.from_str("#006edb")
            """#006edb"""
            muted: Colour = Colour.from_str("#d1f0ff")
            """#d1f0ff"""

        class brown:
            emphasis: Colour = Colour.from_str("#856d4c")
            """#856d4c"""
            muted: Colour = Colour.from_str("#eeeae2")
            """#eeeae2"""

        class coral:
            emphasis: Colour = Colour.from_str("#d43511")
            """#d43511"""
            muted: Colour = Colour.from_str("#ffe5db")
            """#ffe5db"""

        class grey:  # 808fa3, e8ecf2
            emphasis: Colour = Colour.from_str("#808fa3")
            """#808fa3"""
            muted: Colour = Colour.from_str("#e8ecf2")
            """#e8ecf2"""

        class green:  # 30a147 caf7ca
            emphasis: Colour = Colour.from_str("#30a147")
            """#30a147"""
            muted: Colour = Colour.from_str("#caf7ca")
            """#caf7ca"""

        class lemon:  # 866e04 f7eea1
            emphasis: Colour = Colour.from_str("#866e04")
            """#866e04"""
            muted: Colour = Colour.from_str("#f7eea1")
            """#f7eea1"""

        class lime:  # 527a29 e3f2b5
            emphasis: Colour = Colour.from_str("#527a29")
            """#527a29"""
            muted: Colour = Colour.from_str("#e3f2b5")
            """#e3f2b5"""

        class olive:  # 64762d f0f0ad
            emphasis: Colour = Colour.from_str("#64762d")
            """#64762d"""
            muted: Colour = Colour.from_str("#f0f0ad")
            """#f0f0ad"""

        class orange:  # eb670f ffe7d1
            emphasis: Colour = Colour.from_str("#eb670f")
            """#eb670f"""
            muted: Colour = Colour.from_str("#ffe7d1")
            """#ffe7d1"""

        class pine:  # 167e53 bff8db
            emphasis: Colour = Colour.from_str("#167e53")
            """#167e53"""
            muted: Colour = Colour.from_str("#bff8db")
            """#bff8db"""

        class pink:  # ce2c85 ffe5f1
            emphasis: Colour = Colour.from_str("#ce2c85")
            """#ce2c85"""
            muted: Colour = Colour.from_str("#ffe5f1")
            """#ffe5f1"""

        class plum:  # a830e8 f8e5ff
            emphasis: Colour = Colour.from_str("#a830e8")
            """#a830e8"""
            muted: Colour = Colour.from_str("#f8e5ff")
            """#f8e5ff"""

        class purple:  # 894ceb f1e5ff
            emphasis: Colour = Colour.from_str("#894ceb")
            """#894ceb"""
            muted: Colour = Colour.from_str("#f1e5ff")
            """#f1e5ff"""

        class red:  # df0c24 ffe2e0
            emphasis: Colour = Colour.from_str("#df0c24")
            """#df0c24"""
            muted: Colour = Colour.from_str("#ffe2e0")
            """#ffe2e0"""

        class teal:  # 179b9b c7f5ef
            emphasis: Colour = Colour.from_str("#179b9b")
            """#179b9b"""
            muted: Colour = Colour.from_str("#c7f5ef")
            """#c7f5ef"""

        class yellow:  # b88700 ffec9e
            emphasis: Colour = Colour.from_str("#b88700")
            """#b88700"""
            muted: Colour = Colour.from_str("#ffec9e")
            """#ffec9e"""


# Source: https://raw.githubusercontent.com/ozh/github-colors/refs/heads/master/colors.json
GITHUB_LANG2COLOUR: dict[str, Colour] = {
    "1C Enterprise": Colour.from_str("#814CCC"),
    "2-Dimensional Array": Colour.from_str("#38761D"),
    "4D": Colour.from_str("#004289"),
    "ABAP": Colour.from_str("#E8274B"),
    "ABAP CDS": Colour.from_str("#555e25"),
    "ActionScript": Colour.from_str("#882B0F"),
    "Ada": Colour.from_str("#02f88c"),
    "Adblock Filter List": Colour.from_str("#800000"),
    "Adobe Font Metrics": Colour.from_str("#fa0f00"),
    "Agda": Colour.from_str("#315665"),
    "AGS Script": Colour.from_str("#B9D9FF"),
    "AIDL": Colour.from_str("#34EB6B"),
    "Aiken": Colour.from_str("#640ff8"),
    "AL": Colour.from_str("#3AA2B5"),
    "ALGOL": Colour.from_str("#D1E0DB"),
    "Alloy": Colour.from_str("#64C800"),
    "Alpine Abuild": Colour.from_str("#0D597F"),
    "Altium Designer": Colour.from_str("#A89663"),
    "AMPL": Colour.from_str("#E6EFBB"),
    "AngelScript": Colour.from_str("#C7D7DC"),
    "Answer Set Programming": Colour.from_str("#A9CC29"),
    "Ant Build System": Colour.from_str("#A9157E"),
    "Antlers": Colour.from_str("#ff269e"),
    "ANTLR": Colour.from_str("#9DC3FF"),
    "ApacheConf": Colour.from_str("#d12127"),
    "Apex": Colour.from_str("#1797c0"),
    "API Blueprint": Colour.from_str("#2ACCA8"),
    "APL": Colour.from_str("#5A8164"),
    "Apollo Guidance Computer": Colour.from_str("#0B3D91"),
    "AppleScript": Colour.from_str("#101F1F"),
    "Arc": Colour.from_str("#aa2afe"),
    "AsciiDoc": Colour.from_str("#73a0c5"),
    "ASL": GithubColour.github_green,
    "ASP.NET": Colour.from_str("#9400ff"),
    "AspectJ": Colour.from_str("#a957b0"),
    "Assembly": Colour.from_str("#6E4C13"),
    "Astro": Colour.from_str("#ff5a03"),
    "Asymptote": Colour.from_str("#ff0000"),
    "ATS": Colour.from_str("#1ac620"),
    "Augeas": Colour.from_str("#9CC134"),
    "AutoHotkey": Colour.from_str("#6594b9"),
    "AutoIt": Colour.from_str("#1C3552"),
    "Avro IDL": Colour.from_str("#0040FF"),
    "Awk": Colour.from_str("#c30e9b"),
    "B (Formal Method)": Colour.from_str("#8aa8c5"),
    "B4X": Colour.from_str("#00e4ff"),
    "Ballerina": Colour.from_str("#FF5000"),
    "BAML": Colour.from_str("#a855f7"),
    "BASIC": Colour.from_str("#ff0000"),
    "Batchfile": Colour.from_str("#C1F12E"),
    "Beef": Colour.from_str("#a52f4e"),
    "Befunge": GithubColour.github_green,
    "Berry": Colour.from_str("#15A13C"),
    "BibTeX": Colour.from_str("#778899"),
    "BibTeX Style": GithubColour.github_green,
    "Bicep": Colour.from_str("#519aba"),
    "Bikeshed": Colour.from_str("#5562ac"),
    "Bison": Colour.from_str("#6A463F"),
    "BitBake": Colour.from_str("#00bce4"),
    "Blade": Colour.from_str("#f7523f"),
    "BlitzBasic": Colour.from_str("#00FFAE"),
    "BlitzMax": Colour.from_str("#cd6400"),
    "Blueprint": Colour.from_str("#3584E4"),
    "Bluespec": Colour.from_str("#12223c"),
    "Bluespec BH": Colour.from_str("#12223c"),
    "Boo": Colour.from_str("#d4bec1"),
    "Boogie": Colour.from_str("#c80fa0"),
    "BQN": Colour.from_str("#2b7067"),
    "Brainfuck": Colour.from_str("#2F2530"),
    "BrighterScript": Colour.from_str("#66AABB"),
    "Brightscript": Colour.from_str("#662D91"),
    "Browserslist": Colour.from_str("#ffd539"),
    "Bru": Colour.from_str("#F4AA41"),
    "BuildStream": Colour.from_str("#006bff"),
    "C": Colour.from_str("#555555"),
    "C#": Colour.from_str("#7355dd"),
    "C++": Colour.from_str("#f34b7d"),
    "C2hs Haskell": GithubColour.github_green,
    "C3": Colour.from_str("#2563eb"),
    "Cabal Config": Colour.from_str("#483465"),
    "Caddyfile": Colour.from_str("#22b638"),
    "Cadence": Colour.from_str("#00ef8b"),
    "Cairo": Colour.from_str("#ff4a48"),
    "Cairo Zero": Colour.from_str("#ff4a48"),
    "CameLIGO": Colour.from_str("#3be133"),
    "Cangjie": Colour.from_str("#00868B"),
    "CAP CDS": Colour.from_str("#0092d1"),
    "Cap'n Proto": Colour.from_str("#c42727"),
    "Carbon": Colour.from_str("#222222"),
    "CartoCSS": GithubColour.github_green,
    "Ceylon": Colour.from_str("#dfa535"),
    "Chapel": Colour.from_str("#8dc63f"),
    "Charity": GithubColour.github_green,
    "ChucK": Colour.from_str("#3f8000"),
    "Circom": Colour.from_str("#707575"),
    "Cirru": Colour.from_str("#ccccff"),
    "Clarion": Colour.from_str("#db901e"),
    "Clarity": Colour.from_str("#5546ff"),
    "Classic ASP": Colour.from_str("#6a40fd"),
    "Clean": Colour.from_str("#3F85AF"),
    "Click": Colour.from_str("#E4E6F3"),
    "CLIPS": Colour.from_str("#00A300"),
    "Clojure": Colour.from_str("#db5855"),
    "Closure Templates": Colour.from_str("#0d948f"),
    "Cloud Firestore Security Rules": Colour.from_str("#FFA000"),
    "Clue": Colour.from_str("#0009b5"),
    "CMake": Colour.from_str("#DA3434"),
    "COBOL": GithubColour.github_green,
    "CodeQL": Colour.from_str("#140f46"),
    "CoffeeScript": Colour.from_str("#244776"),
    "ColdFusion": Colour.from_str("#ed2cd6"),
    "ColdFusion CFC": Colour.from_str("#ed2cd6"),
    "COLLADA": Colour.from_str("#F1A42B"),
    "Common Lisp": Colour.from_str("#3fb68b"),
    "Common Workflow Language": Colour.from_str("#B5314C"),
    "Component Pascal": Colour.from_str("#B0CE4E"),
    "Cooklang": Colour.from_str("#E15A29"),
    "Cool": GithubColour.github_green,
    "CQL": Colour.from_str("#006091"),
    "crontab": Colour.from_str("#ead7ac"),
    "Crystal": Colour.from_str("#000100"),
    "CSON": Colour.from_str("#244776"),
    "Csound": Colour.from_str("#1a1a1a"),
    "Csound Document": Colour.from_str("#1a1a1a"),
    "Csound Score": Colour.from_str("#1a1a1a"),
    "CSS": Colour.from_str("#663399"),
    "CSV": Colour.from_str("#237346"),
    "Cuda": Colour.from_str("#3A4E3A"),
    "CUE": Colour.from_str("#5886E1"),
    "Curry": Colour.from_str("#531242"),
    "CWeb": Colour.from_str("#00007a"),
    "Cycript": GithubColour.github_green,
    "Cylc": Colour.from_str("#00b3fd"),
    "Cypher": Colour.from_str("#34c0eb"),
    "Cython": Colour.from_str("#fedf5b"),
    "D": Colour.from_str("#ba595e"),
    "D2": Colour.from_str("#526ee8"),
    "Dafny": Colour.from_str("#FFEC25"),
    "Darcs Patch": Colour.from_str("#8eff23"),
    "Dart": Colour.from_str("#00B4AB"),
    "Daslang": Colour.from_str("#d3d3d3"),
    "DataWeave": Colour.from_str("#003a52"),
    "Debian Package Control File": Colour.from_str("#D70751"),
    "DenizenScript": Colour.from_str("#FBEE96"),
    "Dhall": Colour.from_str("#dfafff"),
    "DIGITAL Command Language": GithubColour.github_green,
    "DirectX 3D File": Colour.from_str("#aace60"),
    "DM": Colour.from_str("#447265"),
    "Dockerfile": Colour.from_str("#384d54"),
    "Dogescript": Colour.from_str("#cca760"),
    "Dotenv": Colour.from_str("#e5d559"),
    "DTrace": GithubColour.github_green,
    "Dune": Colour.from_str("#89421e"),
    "Dylan": Colour.from_str("#6c616e"),
    "E": Colour.from_str("#ccce35"),
    "Earthly": Colour.from_str("#2af0ff"),
    "Easybuild": Colour.from_str("#069406"),
    "eC": Colour.from_str("#913960"),
    "Ecere Projects": Colour.from_str("#913960"),
    "ECL": Colour.from_str("#8a1267"),
    "ECLiPSe": Colour.from_str("#001d9d"),
    "Ecmarkup": Colour.from_str("#eb8131"),
    "Edge": Colour.from_str("#0dffe0"),
    "EdgeQL": Colour.from_str("#31A7FF"),
    "EditorConfig": Colour.from_str("#fff1f2"),
    "Eiffel": Colour.from_str("#4d6977"),
    "EJS": Colour.from_str("#a91e50"),
    "Elixir": Colour.from_str("#6e4a7e"),
    "Elm": Colour.from_str("#60B5CC"),
    "Elvish": Colour.from_str("#55BB55"),
    "Elvish Transcript": Colour.from_str("#55BB55"),
    "Emacs Lisp": Colour.from_str("#c065db"),
    "EmberScript": Colour.from_str("#FFF4F3"),
    "EQ": Colour.from_str("#a78649"),
    "Erlang": Colour.from_str("#B83998"),
    "Euphoria": Colour.from_str("#FF790B"),
    "F#": Colour.from_str("#b845fc"),
    "F*": Colour.from_str("#572e30"),
    "Factor": Colour.from_str("#636746"),
    "Fancy": Colour.from_str("#7b9db4"),
    "Fantom": Colour.from_str("#14253c"),
    "Faust": Colour.from_str("#c37240"),
    "Fennel": Colour.from_str("#fff3d7"),
    "FIGlet Font": Colour.from_str("#FFDDBB"),
    "Filebench WML": Colour.from_str("#F6B900"),
    "Filterscript": GithubColour.github_green,
    "FIRRTL": Colour.from_str("#2f632f"),
    "fish": Colour.from_str("#4aae47"),
    "FlatBuffers": Colour.from_str("#ed284a"),
    "Flix": Colour.from_str("#d44a45"),
    "Fluent": Colour.from_str("#ffcc33"),
    "FLUX": Colour.from_str("#88ccff"),
    "Forth": Colour.from_str("#341708"),
    "Fortran": Colour.from_str("#4d41b1"),
    "Fortran Free Form": Colour.from_str("#4d41b1"),
    "FreeBASIC": Colour.from_str("#141AC9"),
    "FreeMarker": Colour.from_str("#0050b2"),
    "Frege": Colour.from_str("#00cafe"),
    "Futhark": Colour.from_str("#5f021f"),
    "G-code": Colour.from_str("#D08CF2"),
    "Game Maker Language": Colour.from_str("#71b417"),
    "GAML": Colour.from_str("#FFC766"),
    "GAMS": Colour.from_str("#f49a22"),
    "GAP": Colour.from_str("#0000cc"),
    "GCC Machine Description": Colour.from_str("#FFCFAB"),
    "GDB": GithubColour.github_green,
    "GDScript": Colour.from_str("#355570"),
    "GDShader": Colour.from_str("#478CBF"),
    "GEDCOM": Colour.from_str("#003058"),
    "Gemfile.lock": Colour.from_str("#701516"),
    "Gemini": Colour.from_str("#ff6900"),
    "Genero 4gl": Colour.from_str("#63408e"),
    "Genero per": Colour.from_str("#d8df39"),
    "Genie": Colour.from_str("#fb855d"),
    "Genshi": Colour.from_str("#951531"),
    "Gentoo Ebuild": Colour.from_str("#9400ff"),
    "Gentoo Eclass": Colour.from_str("#9400ff"),
    "Gerber Image": Colour.from_str("#d20b00"),
    "Gherkin": Colour.from_str("#5B2063"),
    "Git Attributes": Colour.from_str("#F44D27"),
    "Git Commit": Colour.from_str("#F44D27"),
    "Git Config": Colour.from_str("#F44D27"),
    "Git Revision List": Colour.from_str("#F44D27"),
    "Gleam": Colour.from_str("#ffaff3"),
    "Glimmer JS": Colour.from_str("#F5835F"),
    "Glimmer TS": Colour.from_str("#3178c6"),
    "GLSL": Colour.from_str("#5686a5"),
    "Glyph": Colour.from_str("#c1ac7f"),
    "Gnuplot": Colour.from_str("#f0a9f0"),
    "Go": Colour.from_str("#00ADD8"),
    "Go Checksums": Colour.from_str("#00ADD8"),
    "Go Module": Colour.from_str("#00ADD8"),
    "Go Template": Colour.from_str("#00ADD8"),
    "Go Workspace": Colour.from_str("#00ADD8"),
    "Godot Resource": Colour.from_str("#355570"),
    "Golo": Colour.from_str("#88562A"),
    "Gosu": Colour.from_str("#82937f"),
    "Grace": Colour.from_str("#615f8b"),
    "Gradle": Colour.from_str("#02303a"),
    "Gradle Kotlin DSL": Colour.from_str("#02303a"),
    "Grammatical Framework": Colour.from_str("#ff0000"),
    "GraphQL": Colour.from_str("#e10098"),
    "Graphviz (DOT)": Colour.from_str("#2596be"),
    "Groovy": Colour.from_str("#4298b8"),
    "Groovy Server Pages": Colour.from_str("#4298b8"),
    "GSC": Colour.from_str("#FF6800"),
    "GtkRC": Colour.from_str("#7fe719"),
    "Hack": Colour.from_str("#878787"),
    "Haml": Colour.from_str("#ece2a9"),
    "Handlebars": Colour.from_str("#f7931e"),
    "HAProxy": Colour.from_str("#106da9"),
    "Harbour": Colour.from_str("#0e60e3"),
    "Hare": Colour.from_str("#9d7424"),
    "Haskell": Colour.from_str("#5e5086"),
    "Haxe": Colour.from_str("#df7900"),
    "HCL": Colour.from_str("#844FBA"),
    "HIP": Colour.from_str("#4F3A4F"),
    "HiveQL": Colour.from_str("#dce200"),
    "HLSL": Colour.from_str("#aace60"),
    "HOCON": Colour.from_str("#9ff8ee"),
    "HolyC": Colour.from_str("#ffefaf"),
    "hoon": Colour.from_str("#00b171"),
    "Hosts File": Colour.from_str("#308888"),
    "HTML": Colour.from_str("#e34c26"),
    "HTML+ECR": Colour.from_str("#2e1052"),
    "HTML+EEX": Colour.from_str("#6e4a7e"),
    "HTML+ERB": Colour.from_str("#701516"),
    "HTML+PHP": Colour.from_str("#4f5d95"),
    "HTML+Razor": Colour.from_str("#512be4"),
    "HTTP": Colour.from_str("#005C9C"),
    "Hurl": Colour.from_str("#FF0288"),
    "HXML": Colour.from_str("#f68712"),
    "Hy": Colour.from_str("#7790B2"),
    "HyPhy": GithubColour.github_green,
    "iCalendar": Colour.from_str("#ec564c"),
    "IDL": Colour.from_str("#a3522f"),
    "Idris": Colour.from_str("#b30000"),
    "Ignore List": Colour.from_str("#000000"),
    "IGOR Pro": Colour.from_str("#0000cc"),
    "IL Assembly": Colour.from_str("#512BD4"),
    "ImageJ Macro": Colour.from_str("#99AAFF"),
    "Imba": Colour.from_str("#16cec6"),
    "Inform 7": GithubColour.github_green,
    "INI": Colour.from_str("#d1dbe0"),
    "Ink": GithubColour.github_green,
    "Inno Setup": Colour.from_str("#264b99"),
    "Io": Colour.from_str("#a9188d"),
    "Ioke": Colour.from_str("#078193"),
    "Isabelle": Colour.from_str("#FEFE00"),
    "Isabelle ROOT": Colour.from_str("#FEFE00"),
    "ISPC": Colour.from_str("#2D68B1"),
    "J": Colour.from_str("#9EEDFF"),
    "Jac": Colour.from_str("#FC792D"),
    "Jai": Colour.from_str("#ab8b4b"),
    "Janet": Colour.from_str("#0886a5"),
    "JAR Manifest": Colour.from_str("#b07219"),
    "Jasmin": Colour.from_str("#d03600"),
    "Java": Colour.from_str("#b07219"),
    "Java Properties": Colour.from_str("#2A6277"),
    "Java Server Pages": Colour.from_str("#2A6277"),
    "Java Template Engine": Colour.from_str("#2A6277"),
    "JavaScript": Colour.from_str("#f1e05a"),
    "JavaScript+ERB": Colour.from_str("#f1e05a"),
    "JCL": Colour.from_str("#d90e09"),
    "Jest Snapshot": Colour.from_str("#15c213"),
    "JetBrains MPS": Colour.from_str("#21D789"),
    "JFlex": Colour.from_str("#DBCA00"),
    "Jinja": Colour.from_str("#a52a22"),
    "Jison": Colour.from_str("#56b3cb"),
    "Jison Lex": Colour.from_str("#56b3cb"),
    "Jolie": Colour.from_str("#843179"),
    "jq": Colour.from_str("#c7254e"),
    "JSON": Colour.from_str("#292929"),
    "JSON with Comments": Colour.from_str("#292929"),
    "JSON5": Colour.from_str("#267CB9"),
    "JSONiq": Colour.from_str("#40d47e"),
    "JSONLD": Colour.from_str("#0c479c"),
    "Jsonnet": Colour.from_str("#0064bd"),
    "Julia": Colour.from_str("#a270ba"),
    "Julia REPL": Colour.from_str("#a270ba"),
    "Jupyter Notebook": Colour.from_str("#DA5B0B"),
    "Just": Colour.from_str("#384d54"),
    "Kaitai Struct": Colour.from_str("#773b37"),
    "KakouneScript": Colour.from_str("#6f8042"),
    "KCL": Colour.from_str("#7ABABF"),
    "KDL": Colour.from_str("#ffb3b3"),
    "KerboScript": Colour.from_str("#41adf0"),
    "KFramework": Colour.from_str("#4195c5"),
    "KiCad Layout": Colour.from_str("#2f4aab"),
    "KiCad Legacy Layout": Colour.from_str("#2f4aab"),
    "KiCad Schematic": Colour.from_str("#2f4aab"),
    "Koka": Colour.from_str("#215166"),
    "KoLmafia ASH": Colour.from_str("#B9D9B9"),
    "Kotlin": Colour.from_str("#A97BFF"),
    "KRL": Colour.from_str("#28430A"),
    "kvlang": Colour.from_str("#1da6e0"),
    "LabVIEW": Colour.from_str("#fede06"),
    "Lambdapi": Colour.from_str("#8027a3"),
    "Langium": Colour.from_str("#2c8c87"),
    "Lark": Colour.from_str("#2980B9"),
    "Lasso": Colour.from_str("#999999"),
    "Latte": Colour.from_str("#f2a542"),
    "Lean": GithubColour.github_green,
    "Lean 4": GithubColour.github_green,
    "Leo": Colour.from_str("#C4FFC2"),
    "Less": Colour.from_str("#1d365d"),
    "Lex": Colour.from_str("#DBCA00"),
    "LFE": Colour.from_str("#4C3023"),
    "LigoLANG": Colour.from_str("#0e74ff"),
    "LilyPond": Colour.from_str("#9ccc7c"),
    "Limbo": GithubColour.github_green,
    "Linear Programming": GithubColour.github_green,
    "Linker Script": GithubColour.github_green,
    "Liquid": Colour.from_str("#67b8de"),
    "Liquidsoap": Colour.from_str("#990066"),
    "Literate Agda": Colour.from_str("#315665"),
    "Literate CoffeeScript": Colour.from_str("#244776"),
    "Literate Haskell": Colour.from_str("#5e5086"),
    "LiveCode Script": Colour.from_str("#0c5ba5"),
    "LiveScript": Colour.from_str("#499886"),
    "LLVM": Colour.from_str("#185619"),
    "Logos": GithubColour.github_green,
    "Logtalk": Colour.from_str("#295b9a"),
    "LOLCODE": Colour.from_str("#cc9900"),
    "LookML": Colour.from_str("#652B81"),
    "LoomScript": GithubColour.github_green,
    "LSL": Colour.from_str("#3d9970"),
    "Lua": Colour.from_str("#000080"),
    "Luau": Colour.from_str("#00A2FF"),
    "M": GithubColour.github_green,
    "M3U": Colour.from_str("#179C7D"),
    "M4": GithubColour.github_green,
    "M4Sugar": GithubColour.github_green,
    "Macaulay2": Colour.from_str("#d8ffff"),
    "Makefile": Colour.from_str("#427819"),
    "Mako": Colour.from_str("#7e858d"),
    "Markdown": Colour.from_str("#083fa1"),
    "Marko": Colour.from_str("#42bff2"),
    "Mask": Colour.from_str("#f97732"),
    "Mathematical Programming System": Colour.from_str("#0530ad"),
    "MATLAB": Colour.from_str("#e16737"),
    "Max": Colour.from_str("#c4a79c"),
    "MAXScript": Colour.from_str("#00a6a6"),
    "mcfunction": Colour.from_str("#E22837"),
    "mdsvex": Colour.from_str("#5f9ea0"),
    "MDX": Colour.from_str("#fcb32c"),
    "Mercury": Colour.from_str("#ff2b2b"),
    "Mermaid": Colour.from_str("#ff3670"),
    "Meson": Colour.from_str("#007800"),
    "Metal": Colour.from_str("#8f14e9"),
    "MeTTa": Colour.from_str("#6a5acd"),
    "MiniD": GithubColour.github_green,
    "MiniYAML": Colour.from_str("#ff1111"),
    "MiniZinc": Colour.from_str("#06a9e6"),
    "Mint": Colour.from_str("#02b046"),
    "Mirah": Colour.from_str("#c7a938"),
    "mIRC Script": Colour.from_str("#3d57c3"),
    "MLIR": Colour.from_str("#5EC8DB"),
    "Modelica": Colour.from_str("#de1d31"),
    "Modula-2": Colour.from_str("#10253f"),
    "Modula-3": Colour.from_str("#223388"),
    "Module Management System": GithubColour.github_green,
    "Mojo": Colour.from_str("#ff4c1f"),
    "Monkey": GithubColour.github_green,
    "Monkey C": Colour.from_str("#8D6747"),
    "Moocode": GithubColour.github_green,
    "MoonBit": Colour.from_str("#b92381"),
    "MoonScript": Colour.from_str("#ff4585"),
    "Motoko": Colour.from_str("#fbb03b"),
    "Motorola 68K Assembly": Colour.from_str("#005daa"),
    "Move": Colour.from_str("#4a137a"),
    "MQL4": Colour.from_str("#62A8D6"),
    "MQL5": Colour.from_str("#4A76B8"),
    "MTML": Colour.from_str("#b7e1f4"),
    "MUF": GithubColour.github_green,
    "mupad": Colour.from_str("#244963"),
    "Mustache": Colour.from_str("#724b3b"),
    "Myghty": GithubColour.github_green,
    "nanorc": Colour.from_str("#2d004d"),
    "Nasal": Colour.from_str("#1d2c4e"),
    "NASL": GithubColour.github_green,
    "NCL": Colour.from_str("#28431f"),
    "Nearley": Colour.from_str("#990000"),
    "Nemerle": Colour.from_str("#3d3c6e"),
    "nesC": Colour.from_str("#94B0C7"),
    "NetLinx": Colour.from_str("#0aa0ff"),
    "NetLinx+ERB": Colour.from_str("#747faa"),
    "NetLogo": Colour.from_str("#ff6375"),
    "NewLisp": Colour.from_str("#87AED7"),
    "Nextflow": Colour.from_str("#3ac486"),
    "Nginx": Colour.from_str("#009639"),
    "Nickel": Colour.from_str("#E0C3FC"),
    "Nim": Colour.from_str("#ffc200"),
    "Nit": Colour.from_str("#009917"),
    "Nix": Colour.from_str("#7e7eff"),
    "NMODL": Colour.from_str("#00356B"),
    "Noir": Colour.from_str("#2f1f49"),
    "NPM Config": Colour.from_str("#cb3837"),
    "NSIS": GithubColour.github_green,
    "Nu": Colour.from_str("#c9df40"),
    "NumPy": Colour.from_str("#9C8AF9"),
    "Nunjucks": Colour.from_str("#3d8137"),
    "Nushell": Colour.from_str("#4E9906"),
    "NWScript": Colour.from_str("#111522"),
    "OASv2-json": Colour.from_str("#85ea2d"),
    "OASv2-yaml": Colour.from_str("#85ea2d"),
    "OASv3-json": Colour.from_str("#85ea2d"),
    "OASv3-yaml": Colour.from_str("#85ea2d"),
    "Oberon": GithubColour.github_green,
    "Objective-C": Colour.from_str("#438eff"),
    "Objective-C++": Colour.from_str("#6866fb"),
    "Objective-J": Colour.from_str("#ff0c5a"),
    "ObjectScript": Colour.from_str("#424893"),
    "OCaml": Colour.from_str("#ef7a08"),
    "Odin": Colour.from_str("#60AFFE"),
    "Omgrofl": Colour.from_str("#cabbff"),
    "OMNeT++ MSG": Colour.from_str("#a0e0a0"),
    "OMNeT++ NED": Colour.from_str("#08607c"),
    "ooc": Colour.from_str("#b0b77e"),
    "Opa": GithubColour.github_green,
    "Opal": Colour.from_str("#f7ede0"),
    "Open Policy Agent": Colour.from_str("#7d9199"),
    "OpenAPI Specification v2": Colour.from_str("#85ea2d"),
    "OpenAPI Specification v3": Colour.from_str("#85ea2d"),
    "OpenCL": Colour.from_str("#ed2e2d"),
    "OpenEdge ABL": Colour.from_str("#5ce600"),
    "OpenQASM": Colour.from_str("#AA70FF"),
    "OpenRC runscript": GithubColour.github_green,
    "OpenSCAD": Colour.from_str("#e5cd45"),
    "Option List": Colour.from_str("#476732"),
    "Org": Colour.from_str("#77aa99"),
    "OverpassQL": Colour.from_str("#cce2aa"),
    "OverPy": Colour.from_str("#78b355"),
    "Ox": GithubColour.github_green,
    "Oxygene": Colour.from_str("#cdd0e3"),
    "Oz": Colour.from_str("#fab738"),
    "P4": Colour.from_str("#7055b5"),
    "Pact": Colour.from_str("#F7A8B8"),
    "Pan": Colour.from_str("#cc0000"),
    "Papyrus": Colour.from_str("#6600cc"),
    "Parrot": Colour.from_str("#f3ca0a"),
    "Parrot Assembly": GithubColour.github_green,
    "Parrot Internal Representation": GithubColour.github_green,
    "Pascal": Colour.from_str("#E3F171"),
    "Pawn": Colour.from_str("#dbb284"),
    "PDDL": Colour.from_str("#0d00ff"),
    "PEG.js": Colour.from_str("#234d6b"),
    "Pep8": Colour.from_str("#C76F5B"),
    "Perl": Colour.from_str("#0298c3"),
    "PHP": Colour.from_str("#4F5D95"),
    "PicoLisp": Colour.from_str("#6067af"),
    "PigLatin": Colour.from_str("#fcd7de"),
    "Pike": Colour.from_str("#005390"),
    "Pip Requirements": Colour.from_str("#FFD343"),
    "pkg-config": Colour.from_str("#2b5e82"),
    "Pkl": Colour.from_str("#6b9543"),
    "PlantUML": Colour.from_str("#fbbd16"),
    "PLpgSQL": Colour.from_str("#336790"),
    "PLSQL": Colour.from_str("#dad8d8"),
    "PogoScript": Colour.from_str("#d80074"),
    "Polar": Colour.from_str("#ae81ff"),
    "Pony": GithubColour.github_green,
    "Portugol": Colour.from_str("#f8bd00"),
    "PostCSS": Colour.from_str("#dc3a0c"),
    "PostScript": Colour.from_str("#da291c"),
    "POV-Ray SDL": Colour.from_str("#6bac65"),
    "Power Query": Colour.from_str("#d38e0d"),
    "PowerBuilder": Colour.from_str("#8f0f8d"),
    "PowerShell": Colour.from_str("#012456"),
    "Praat": Colour.from_str("#c8506d"),
    "Prisma": Colour.from_str("#0c344b"),
    "Pro*C": Colour.from_str("#bb8368"),
    "Processing": Colour.from_str("#0096D8"),
    "Procfile": Colour.from_str("#3B2F63"),
    "Prolog": Colour.from_str("#74283c"),
    "Promela": Colour.from_str("#de0000"),
    "Propeller Spin": Colour.from_str("#7fa2a7"),
    "Pug": Colour.from_str("#a86454"),
    "Puppet": Colour.from_str("#302B6D"),
    "PureBasic": Colour.from_str("#5a6986"),
    "PureScript": Colour.from_str("#1D222D"),
    "Pyret": Colour.from_str("#ee1e10"),
    "Python": Colour.from_str("#3572A5"),
    "Python console": Colour.from_str("#3572A5"),
    "Python traceback": Colour.from_str("#3572A5"),
    "q": Colour.from_str("#0040cd"),
    "Q#": Colour.from_str("#fed659"),
    "QMake": GithubColour.github_green,
    "QML": Colour.from_str("#44a51c"),
    "Qt Script": Colour.from_str("#00b841"),
    "Quake": Colour.from_str("#882233"),
    "QuakeC": Colour.from_str("#975777"),
    "QuickBASIC": Colour.from_str("#008080"),
    "Quint": Colour.from_str("#9d6ce5"),
    "R": Colour.from_str("#198CE7"),
    "Racket": Colour.from_str("#3c5caa"),
    "Ragel": Colour.from_str("#9d5200"),
    "Raku": Colour.from_str("#0000fb"),
    "RAML": Colour.from_str("#77d9fb"),
    "Rascal": Colour.from_str("#fffaa0"),
    "RAScript": Colour.from_str("#2C97FA"),
    "RBS": Colour.from_str("#701516"),
    "RDoc": Colour.from_str("#701516"),
    "REALbasic": GithubColour.github_green,
    "Reason": Colour.from_str("#ff5847"),
    "ReasonLIGO": Colour.from_str("#ff5847"),
    "Rebol": Colour.from_str("#358a5b"),
    "Record Jar": Colour.from_str("#0673ba"),
    "Red": Colour.from_str("#f50000"),
    "Redcode": GithubColour.github_green,
    "Redscript": Colour.from_str("#f44336"),
    "Regular Expression": Colour.from_str("#009a00"),
    "Ren'Py": Colour.from_str("#ff7f7f"),
    "RenderScript": GithubColour.github_green,
    "ReScript": Colour.from_str("#ed5051"),
    "reStructuredText": Colour.from_str("#141414"),
    "REXX": Colour.from_str("#d90e09"),
    "Rez": Colour.from_str("#FFDAB3"),
    "Ring": Colour.from_str("#2D54CB"),
    "Riot": Colour.from_str("#A71E49"),
    "RMarkdown": Colour.from_str("#198ce7"),
    "RobotFramework": Colour.from_str("#00c0b5"),
    "Roc": Colour.from_str("#7c38f5"),
    "Rocq Prover": Colour.from_str("#d0b68c"),
    "Roff": Colour.from_str("#ecdebe"),
    "Roff Manpage": Colour.from_str("#ecdebe"),
    "RON": Colour.from_str("#a62c00"),
    "ROS Interface": Colour.from_str("#22314e"),
    "Rouge": Colour.from_str("#cc0088"),
    "RouterOS Script": Colour.from_str("#DE3941"),
    "RPC": GithubColour.github_green,
    "RPGLE": Colour.from_str("#2BDE21"),
    "Ruby": Colour.from_str("#701516"),
    "RUNOFF": Colour.from_str("#665a4e"),
    "Rust": Colour.from_str("#dea584"),
    "Sage": GithubColour.github_green,
    "Sail": Colour.from_str("#259dd5"),
    "SaltStack": Colour.from_str("#646464"),
    "SAS": Colour.from_str("#B34936"),
    "Sass": Colour.from_str("#a53b70"),
    "Scala": Colour.from_str("#c22d40"),
    "Scaml": Colour.from_str("#bd181a"),
    "Scenic": Colour.from_str("#fdc700"),
    "Scheme": Colour.from_str("#1e4aec"),
    "Scilab": Colour.from_str("#ca0f21"),
    "SCSS": Colour.from_str("#c6538c"),
    "sed": Colour.from_str("#64b970"),
    "Self": Colour.from_str("#0579aa"),
    "ShaderLab": Colour.from_str("#222c37"),
    "Shell": Colour.from_str("#89e051"),
    "ShellCheck Config": Colour.from_str("#cecfcb"),
    "ShellSession": GithubColour.github_green,
    "Shen": Colour.from_str("#120F14"),
    "Sieve": GithubColour.github_green,
    "Simple File Verification": Colour.from_str("#C9BFED"),
    "Singularity": Colour.from_str("#64E6AD"),
    "Slang": Colour.from_str("#1fbec9"),
    "Slash": Colour.from_str("#007eff"),
    "Slice": Colour.from_str("#003fa2"),
    "Slim": Colour.from_str("#2b2b2b"),
    "Slint": Colour.from_str("#2379F4"),
    "Smali": GithubColour.github_green,
    "Smalltalk": Colour.from_str("#596706"),
    "Smarty": Colour.from_str("#f0c040"),
    "Smithy": Colour.from_str("#c44536"),
    "SmPL": Colour.from_str("#c94949"),
    "SMT": GithubColour.github_green,
    "Snakemake": Colour.from_str("#419179"),
    "Solidity": Colour.from_str("#AA6746"),
    "SourcePawn": Colour.from_str("#f69e1d"),
    "SPARQL": Colour.from_str("#0C4597"),
    "SpiceDB Schema": Colour.from_str("#a5318a"),
    "SQF": Colour.from_str("#3F3F3F"),
    "SQL": Colour.from_str("#e38c00"),
    "SQLPL": Colour.from_str("#e38c00"),
    "Squirrel": Colour.from_str("#800000"),
    "SRecode Template": Colour.from_str("#348a34"),
    "Stan": Colour.from_str("#b2011d"),
    "Standard ML": Colour.from_str("#dc566d"),
    "Starlark": Colour.from_str("#76d275"),
    "Stata": Colour.from_str("#1a5f91"),
    "STL": Colour.from_str("#373b5e"),
    "StringTemplate": Colour.from_str("#3fb34f"),
    "Stylus": Colour.from_str("#ff6347"),
    "SubRip Text": Colour.from_str("#9e0101"),
    "SugarSS": Colour.from_str("#2fcc9f"),
    "SuperCollider": Colour.from_str("#46390b"),
    "SurrealQL": Colour.from_str("#ff00a0"),
    "Survex data": Colour.from_str("#ffcc99"),
    "Svelte": Colour.from_str("#ff3e00"),
    "SVG": Colour.from_str("#ff9900"),
    "Sway": Colour.from_str("#00F58C"),
    "Sweave": Colour.from_str("#198ce7"),
    "Swift": Colour.from_str("#F05138"),
    "SWIG": GithubColour.github_green,
    "SystemVerilog": Colour.from_str("#DAE1C2"),
    "Tact": Colour.from_str("#48b5ff"),
    "Talon": Colour.from_str("#333333"),
    "Tcl": Colour.from_str("#e4cc98"),
    "Tcsh": GithubColour.github_green,
    "Teal": Colour.from_str("#00B1BC"),
    "templ": Colour.from_str("#66D0DD"),
    "Terra": Colour.from_str("#00004c"),
    "Terraform Template": Colour.from_str("#7b42bb"),
    "TeX": Colour.from_str("#3D6117"),
    "TextGrid": Colour.from_str("#c8506d"),
    "Textile": Colour.from_str("#ffe7ac"),
    "TextMate Properties": Colour.from_str("#df66e4"),
    "Thrift": Colour.from_str("#D12127"),
    "TI Program": Colour.from_str("#A0AA87"),
    "TL-Verilog": Colour.from_str("#C40023"),
    "TLA": Colour.from_str("#4b0079"),
    "TMDL": Colour.from_str("#f0c913"),
    "Toit": Colour.from_str("#c2c9fb"),
    "TOML": Colour.from_str("#9c4221"),
    "Tor Config": Colour.from_str("#59316b"),
    "Tree-sitter Query": Colour.from_str("#8ea64c"),
    "TSQL": Colour.from_str("#e38c00"),
    "TSV": Colour.from_str("#237346"),
    "TSX": Colour.from_str("#3178c6"),
    "Turing": Colour.from_str("#cf142b"),
    "Twig": Colour.from_str("#c1d026"),
    "TXL": Colour.from_str("#0178b8"),
    "TypeScript": Colour.from_str("#3178c6"),
    "TypeSpec": Colour.from_str("#4A3665"),
    "Typst": Colour.from_str("#239dad"),
    "Unified Parallel C": Colour.from_str("#4e3617"),
    "Unity3D Asset": Colour.from_str("#222c37"),
    "Unix Assembly": GithubColour.github_green,
    "Uno": Colour.from_str("#9933cc"),
    "UnrealScript": Colour.from_str("#a54c4d"),
    "Untyped Plutus Core": Colour.from_str("#36adbd"),
    "UrWeb": Colour.from_str("#ccccee"),
    "V": Colour.from_str("#4f87c4"),
    "Vala": Colour.from_str("#a56de2"),
    "Valve Data Format": Colour.from_str("#f26025"),
    "VBA": Colour.from_str("#867db1"),
    "VBScript": Colour.from_str("#15dcdc"),
    "vCard": Colour.from_str("#ee2647"),
    "VCL": Colour.from_str("#148AA8"),
    "Velocity Template Language": Colour.from_str("#507cff"),
    "Vento": Colour.from_str("#ff0080"),
    "Verilog": Colour.from_str("#b2b7f8"),
    "VHDL": Colour.from_str("#adb2cb"),
    "Vim Help File": Colour.from_str("#199f4b"),
    "Vim Script": Colour.from_str("#199f4b"),
    "Vim Snippet": Colour.from_str("#199f4b"),
    "Visual Basic .NET": Colour.from_str("#945db7"),
    "Visual Basic 6.0": Colour.from_str("#2c6353"),
    "Volt": Colour.from_str("#1F1F1F"),
    "Vue": Colour.from_str("#41b883"),
    "Vyper": Colour.from_str("#9F4CF2"),
    "WDL": Colour.from_str("#42f1f4"),
    "Web Ontology Language": Colour.from_str("#5b70bd"),
    "WebAssembly": Colour.from_str("#04133b"),
    "WebAssembly Interface Type": Colour.from_str("#6250e7"),
    "WebIDL": GithubColour.github_green,
    "WGSL": Colour.from_str("#1a5e9a"),
    "Whiley": Colour.from_str("#d5c397"),
    "Wikitext": Colour.from_str("#fc5757"),
    "Windows Registry Entries": Colour.from_str("#52d5ff"),
    "wisp": Colour.from_str("#7582D1"),
    "Witcher Script": Colour.from_str("#ff0000"),
    "Wolfram Language": Colour.from_str("#dd1100"),
    "Wollok": Colour.from_str("#a23738"),
    "World of Warcraft Addon Data": Colour.from_str("#f7e43f"),
    "Wren": Colour.from_str("#383838"),
    "X10": Colour.from_str("#4B6BEF"),
    "xBase": Colour.from_str("#403a40"),
    "XC": Colour.from_str("#99DA07"),
    "Xmake": Colour.from_str("#22a079"),
    "XML": Colour.from_str("#0060ac"),
    "XML Property List": Colour.from_str("#0060ac"),
    "Xojo": Colour.from_str("#81bd41"),
    "Xonsh": Colour.from_str("#285EEF"),
    "XProc": GithubColour.github_green,
    "XQuery": Colour.from_str("#5232e7"),
    "XS": GithubColour.github_green,
    "XSLT": Colour.from_str("#EB8CEB"),
    "Xtend": Colour.from_str("#24255d"),
    "Yacc": Colour.from_str("#4B6C4B"),
    "YAML": Colour.from_str("#cb171e"),
    "YARA": Colour.from_str("#220000"),
    "YASnippet": Colour.from_str("#32AB90"),
    "Yul": Colour.from_str("#794932"),
    "ZAP": Colour.from_str("#0d665e"),
    "Zeek": GithubColour.github_green,
    "ZenScript": Colour.from_str("#00BCD1"),
    "Zephir": Colour.from_str("#118f9e"),
    "Zig": Colour.from_str("#ec915c"),
    "ZIL": Colour.from_str("#dc75e5"),
    "Zimpl": Colour.from_str("#d67711"),
    "Zmodel": Colour.from_str("#ff7100"),
}
