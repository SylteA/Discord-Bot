from datetime import datetime

from pydantic import Field

from .model import Model


class Tag(Model):
    id: int
    guild_id: int
    author_id: int
    content: str
    name: str
    uses: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    deleted: bool = False

    @classmethod
    async def create(cls, guild_id: int, author_id: int, name: str, content: str) -> "Tag":
        query = """
            INSERT INTO tags (guild_id, author_id, name, content, uses)
                 VALUES ($1, $2, $3, $4, 0)
              RETURNING *;
        """
        return await cls.fetchrow(query, guild_id, author_id, name, content)

    @classmethod
    async def fetch_by_name(cls, guild_id: int, name: str) -> "Tag | None":
        """Fetches the specified tag, if it exists."""
        query = """
            SELECT *
              FROM tags
             WHERE guild_id = $1
               AND name = $2
        """

        return await cls.fetchrow(query, guild_id, name)

    @classmethod
    async def fetch_by_id(cls, guild_id: int, tag_id: int) -> "Tag | None":
        """Fetches the specified tag, if it exists."""
        query = """
            SELECT *
              FROM tags
             WHERE guild_id = $1
               AND id = $2
        """

        return await cls.fetchrow(query, guild_id, tag_id)

    async def delete(self) -> bool:
        """Returns whether the tag was deleted"""
        query = "DELETE FROM tags WHERE id = $1"
        status = await Tag.execute(query, self.id)

        if status[-1] == "1":
            self.deleted = True

        return self.deleted

    async def edit(self, name: str, content: str) -> "Tag":
        """Update the name and content of this tag."""
        query = """
            UPDATE tags
               SET name = $2, content = $3
             WHERE id = $1
         RETURNING *
        """

        return await self.fetchrow(query, self.id, name, content)
