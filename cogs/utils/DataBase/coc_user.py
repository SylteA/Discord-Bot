class CocUser:
    discord_id: int
    coc_id: str
    wins: int

    def __init__(self, bot, *, discord_id: int, coc_id: str, wins: int = 0):
        self.bot = bot
        self.discord_id = discord_id
        self.coc_id = coc_id
        self.wins = wins

    def __repr__(self):
        return (f"<CocUser discord_id={repr(self.discord_id)} "
                f"coc_id={repr(self.coc_id)} wins={repr(self.wins)}>")
