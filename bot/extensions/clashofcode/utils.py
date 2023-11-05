import codingame


class ClashOfCodeHelper:
    def __init__(self):
        self.session = False
        self.last_clash = 0


coc_helper = ClashOfCodeHelper()
coc_client = codingame.Client(is_async=True)

languages = [
    "Bash",
    "C",
    "C#",
    "C++",
    "Clojure",
    "D",
    "Dart",
    "Go",
    "Groovy",
    "Haskell",
    "Java",
    "Javascript",
    "Kotlin",
    "Lua",
    "ObjectiveC",
    "OCaml",
    "Pascal",
    "Perl",
    "PHP",
    "Python3",
    "Ruby",
    "Rust",
    "Scala",
    "Swift",
    "TypeScript",
]
modes = ["FASTEST", "SHORTEST", "REVERSE"]
