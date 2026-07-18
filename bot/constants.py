import discord

region_map: dict[str, str] = {
    "brazil": "Brazil",
    "eu-central": "Central Europe",
    "hongkong": "Hong Kong",
    "japan": "Japan",
    "russia": "Russia",
    "singapore": "Singapore",
    "sydney": "Sydney",
    "us-central": "Central United States",
    "us-east": "Eastern United States",
    "us-south": "Southern United States",
    "us-west": "Western United States",
    "eu-west": "Western Europe",
    "vip-amsterdam": "Amsterdam (VIP)",
    "vip-us-east": "Eastern United States (VIP)",
    "india": "India",
    "europe": "Europe",
    "southafrica": "South Africa",
    "frankfurt": "Frankfurt",
    "south-korea": "South Korea",
    "london": "London",
    "amsterdam": "Amsterdam",
}

sorted_cats: list[str] = [
    "Bot Admin",
    "LaTeX",
    "Guild Admin",
    "Info",
    "Utility",
    "Fun",
    "Mahjong",
    "Moderation",
    "Maths",
    "Meta",
    "Misc",
]

sorted_conf_pages: list[tuple[str, list[str]]] = [
    ("General", ["Guild settings", "Starboard", "LaTeX"]),
    ("Manual Moderation", ["Moderation", "Logging"]),
    ("Join/Leave Messages", ["Join message", "Leave message"]),
]

ParaCC: dict[str, discord.Colour] = {
    "purple": discord.Colour(int("7927eb", 16)),
    "blue": discord.Colour(int("00a7fe", 16)),
}
LuaTeXitCC: dict[str, discord.Colour] = {
    "red": discord.Colour.from_str("#BC0909"),
    "green": discord.Colour.from_str("#5EB859"),
    "yellow": discord.Colour.from_str("#FFC107"),
    "purple": discord.Colour.from_str("#C073E5"),
    "blue": discord.Colour.from_str("#69A2CC"),
    "white": discord.Colour.from_str("#EBE9E2"),
    "cyan": discord.Colour.from_str("#3194A5"),
}
