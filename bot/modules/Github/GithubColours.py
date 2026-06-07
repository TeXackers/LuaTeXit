import discord
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
            
            class open:
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
        
        class grey: # 808fa3, e8ecf2
            emphasis: Colour = Colour.from_str("#808fa3")
            """#808fa3"""
            muted: Colour = Colour.from_str("#e8ecf2")
            """#e8ecf2"""
        
        class green: # 30a147 caf7ca
            emphasis: Colour = Colour.from_str("#30a147")
            """#30a147"""
            muted: Colour = Colour.from_str("#caf7ca")
            """#caf7ca"""
        
        class lemon: # 866e04 f7eea1
            emphasis: Colour = Colour.from_str("#866e04")
            """#866e04"""
            muted: Colour = Colour.from_str("#f7eea1")
            """#f7eea1"""
        
        class lime: # 527a29 e3f2b5
            emphasis: Colour = Colour.from_str("#527a29")
            """#527a29"""
            muted: Colour = Colour.from_str("#e3f2b5")
            """#e3f2b5"""

        class olive: # 64762d f0f0ad
            emphasis: Colour = Colour.from_str("#64762d")
            """#64762d"""
            muted: Colour = Colour.from_str("#f0f0ad")
            """#f0f0ad"""
        
        class orange: # eb670f ffe7d1
            emphasis: Colour = Colour.from_str("#eb670f")
            """#eb670f"""
            muted: Colour = Colour.from_str("#ffe7d1")
            """#ffe7d1"""
        
        class pine: # 167e53 bff8db
            emphasis: Colour = Colour.from_str("#167e53")
            """#167e53"""
            muted: Colour = Colour.from_str("#bff8db")
            """#bff8db"""

        class pink: # ce2c85 ffe5f1
            emphasis: Colour = Colour.from_str("#ce2c85")
            """#ce2c85"""
            muted: Colour = Colour.from_str("#ffe5f1")
            """#ffe5f1"""
        
        class plum: # a830e8 f8e5ff
            emphasis: Colour = Colour.from_str("#a830e8")
            """#a830e8"""
            muted: Colour = Colour.from_str("#f8e5ff")
            """#f8e5ff"""
        
        class purple: # 894ceb f1e5ff
            emphasis: Colour = Colour.from_str("#894ceb")
            """#894ceb"""
            muted: Colour = Colour.from_str("#f1e5ff")
            """#f1e5ff"""
        
        class red: # df0c24 ffe2e0
            emphasis: Colour = Colour.from_str("#df0c24")
            """#df0c24"""
            muted: Colour = Colour.from_str("#ffe2e0")
            """#ffe2e0"""
        
        class teal: # 179b9b c7f5ef
            emphasis: Colour = Colour.from_str("#179b9b")
            """#179b9b"""
            muted: Colour = Colour.from_str("#c7f5ef")
            """#c7f5ef"""
        
        class yellow: # b88700 ffec9e
            emphasis: Colour = Colour.from_str("#b88700")
            """#b88700"""
            muted: Colour = Colour.from_str("#ffec9e")
            """#ffec9e"""