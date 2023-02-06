from datetime import datetime
from typing import Optional

from pydantic import Field

from .model import Model


class Tag(Model):
    guild_id: int
    creator_id: int
    text: str
    name: str
    uses: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    async def fetch_tag(cls, guild_id: int, name: str) -> Optional["Tag"]:
        query = """SELECT * FROM tags WHERE guild_id = $1 AND name = $2"""
        return await cls.fetchrow(query, guild_id, name)

    async def post(self):
        query = """INSERT INTO tags ( guild_id, creator_id, text, name, uses, created_at )
                   VALUES ( $1, $2, $3, $4, $5, $6 )"""
        await self.execute(
            query,
            self.guild_id,
            self.creator_id,
            self.text,
            self.name,
            self.uses,
            self.created_at,
        )

    async def update(self, text):
        self.text = text
        query = """UPDATE tags SET text = $2 WHERE guild_id = $1 AND name = $3"""
        await self.execute(query, self.guild_id, self.text, self.name)

    async def delete(self):
        query = """DELETE FROM tags WHERE guild_id = $1 AND name = $2"""
        await self.execute(query, self.guild_id, self.name)

    async def rename(self, new_name):
        query = """UPDATE tags SET name = $3 WHERE guild_id = $1 AND name = $2"""
        await self.execute(query, self.guild_id, self.name, new_name)
