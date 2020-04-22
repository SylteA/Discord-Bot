from datetime import datetime


class Tag:
    def __init__(self, bot, guild_id: int, creator_id: int, text: str, name: str, uses: int = 0,
                 created_at: datetime = datetime.utcnow()):

        self.bot = bot
        self.guild_id = guild_id
        self.creator_id = creator_id
        self.text = text
        self.name = name.lower()
        self.uses = uses
        self.created_at = created_at

    async def post(self):
        query = """INSERT INTO tags ( guild_id, creator_id, text, name, uses, created_at )
                   VALUES ( $1, $2, $3, $4, $5, $6 )"""
        await self.bot.db.execute(query, self.guild_id, self.creator_id, self.text, self.name, self.uses, self.created_at)

    async def update(self, text):
        self.text = text
        query = """UPDATE tags SET text = $2 WHERE guild_id = $1 AND name = $3"""
        await self.bot.db.execute(query, self.guild_id, self.text, self.name)

    async def delete(self):
        query = """DELETE FROM tags WHERE guild_id = $1 AND name = $2"""
        await self.bot.db.execute(query, self.guild_id, self.name)
