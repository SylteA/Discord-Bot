import typing

import codingame

if typing.TYPE_CHECKING:
    import discord


class ClashOfCodeHelper:
    def __init__(self):
        self.session = False
        self.clash = None
        self.last_clash = 0
        self.host: discord.Member | None = None
        self.message: discord.Message | None = None
        self.languages: list[str] | None = None
        self.modes: list[str] | None = None
        self.handle: str | None = None


coc_helper = ClashOfCodeHelper()
coc_client = codingame.Client(is_async=True)
# fmt: off
languages = [
    "Bash",  "C",          "C#",     "C++",    "Clojure",
    "D",     "Dart",       "Go",     "Groovy", "Haskell",
    "Java",  "Javascript", "Kotlin", "Lua",    "ObjectiveC",
    "OCaml", "Pascal",     "Perl",   "PHP",    "Python3",
    "Ruby",  "Rust",       "Scala",  "Swift",  "TypeScript",
]
# fmt: on
modes = ["FASTEST", "SHORTEST", "REVERSE"]
