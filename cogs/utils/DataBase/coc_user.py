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

    async def post(self):
        query = """INSERT INTO coc_users ( discord_id, coc_id, wins )
                   VALUES ( $1, $2, $3 )"""
        await self.bot.db.execute(query, self.discord_id, self.coc_id, self.wins)

    async def add_win(self):
        self.wins += 1
        query = """UPDATE coc_users SET wins = wins + 1 WHERE coc_id = $1"""
        await self.bot.db.execute(query, self.coc_id)
