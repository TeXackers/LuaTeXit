"""
Dialogues and Output using LayoutView
"""

import random

from discord import Colour
from discord.ui import Container, LayoutView, Section, Separator, TextDisplay, Thumbnail

from .Format import footnote, h3

_error_colour: Colour = Colour.from_rgb(197, 50, 17)

# DBD
ERROR_URL_BUILDER: str = "https://deadbydaylight.wiki.gg/images/FulliconStatusEffects_{}&format=original"
ERROR_THUMBNAILS: list[str] = [
    "incapacitated.png?556d85",
    "hindered.png?ae022e",
    "revealed.png?46321e",
    "oblivious.png?a1123f",
    "mangled.png?176f47",
    "madness.png?45e04e",
    "exposed.png?7f9680",
    "glyph.png?846c73",
    "bleeding.png?78b33a",
]

# IRASUTOYA
IRASUTOYA_THUMBNAILS: list[str] = [
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEi5BjbZlPtezs2fv8V4dQViYtwEXo3eeW3qPYtcs4iJTwnKOGkZxN-Rs2WbdgFi-3EnHADBWTfVz80ucSRu89EElRq-mU68Oze7aahmhB12BMnNpoEA_qOqnb9XhTU4kqxb3e92_JHBG0Oi/s800/saigai_randoseru_mamoru.png",  # ランドセルで身を守る子供
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjiMNEA2mOZFcOgMgs_5j9KgvmafI6D3wQls4J6Lj8FvMfAylNM0y7x4o7DKwG_AL2sIDgWdJQ-yJq9AHYMSJi7LIvevFg9NXOwjg84hB2JNDRNwQS5g6_Ia9oqFA5mE4TonW7TtQdQEhPN/s800/shitsuke_shikaru_father.png",  # 真剣に子供を叱るお父さん
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEj229rGvNmAXuLRgslyfo1_hyphenhyphenB0joBFTm2vLv_Oi1jEds3gL0_jUCRuFMkAhiZLmGuQD5q6oDC_NJ8YNwc-sR2Se_dbPs3QE-TZnQWFJFQs0qFZ0Ki2_6LGjWbhfOojEz-lqtRwKKq4-dY/s800/family_hankouki_haha_musume.png",  # 反抗期の娘と母親
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEg0DgyvZFpi3HZXlX_Q7PYd13_Kj7zK1FcqjmsXORaTLJaPVJJ0QoW09BxKvL4lJCqBiTrS1qi9Ntgu96mJSJHWeO7QOQanmC7aP0P8CroFGAbEWrXBWbXucOGNwAVS6ygCMzOG0XX896c/s800/family_hankouki_chichi_musume.png",  # 反抗期の娘と父親
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgGtuU3XBYAJK6SH6ECizt7FqqCrfGI6RZ7mf7yYpoMz3z61jE3pW4V0lUSxX1EO53lLyynX3MgZVP97H8U4ktLqjDkG_PJ6lMTQV8LYtSQQhs8JtB4QC1Ipd3AFhY2JiNUiXHP8-Ons0c/s800/family_hankouki_haha_musuko.png",  # 反抗期の息子と母親
    "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhYIw-DzanMl-53tz-G1xskrypk7rkF1DTjk6J53YNd8M-OQ0VzggVKBdTT77S6Y-eIxugCPeGm07oJr6CxXMRdCf-sYnHspPzEa1EBLFpWyoTu5jK6ex0nuCb58SKel3Ww_fDebl3bbdg/s800/family_hankouki_chichi_musuko.png",  # 反抗期の息子と父親
]


class Header(TextDisplay):
    def __init__(self, text: str) -> None:
        if not text:
            raise ValueError("Header text cannot be empty.")
        super().__init__(f"{h3(text)}")


class Body(TextDisplay):
    def __init__(self, text: str) -> None:
        if not text:
            raise ValueError("Body text cannot be empty.")
        super().__init__(f"\n{text}\n")


class Footer(TextDisplay):
    def __init__(self, text: str) -> None:
        if not text:
            raise ValueError("Footer text cannot be empty.")
        super().__init__(f"\n{footnote(text)}")


class SectionWithThumbnail(Section):
    def __init__(self, text: str, thumbnail_url: str) -> None:
        super().__init__(Body(text), accessory=Thumbnail(thumbnail_url))


class GenericFullEmbed(LayoutView):
    def __init__(self, header: str, body: str, footer: str, thumbnail_url: str, accent_colour: Colour) -> None:
        super().__init__(timeout=6000)

        container = Container(
            Header(header),
            Separator(),
            SectionWithThumbnail(body, thumbnail_url),
            Footer(footer),
            accent_colour=accent_colour,
        )
        self.add_item(container)


class ErrorEmbedView(LayoutView):
    def __init__(self, body_text: str, datetime: str) -> None:
        super().__init__(timeout=None)

        container = Container(
            Header("Error"),
            Separator(),
            SectionWithThumbnail(body_text, random.choice(IRASUTOYA_THUMBNAILS)),
            Footer(datetime),
            accent_colour=_error_colour,
        )
        self.add_item(container)


class DebugEmbedView(LayoutView):
    """LayoutView for an error message that accompanies a codeblock. Useful for when a command fails and you want to output the error message in a codeblock with a nice layout."""

    def __init__(self, helper_text: str, exception_text: str, datetime: str) -> None:
        super().__init__(timeout=None)

        # check if exception text is already in a codeblock with python syntax.
        if not exception_text.startswith("```") and not exception_text.endswith("```"):
            exception_text = f"```python\n{exception_text}\n```"

        container = Container(
            Header("Unexpected Error"),
            Separator(),
            SectionWithThumbnail(helper_text, random.choice(IRASUTOYA_THUMBNAILS)),
            Body(exception_text),
            Footer(datetime),
            accent_colour=Colour.from_rgb(219, 157, 0),
        )
        self.add_item(container)
