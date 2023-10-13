from typing import Optional

from .model import Model


class PersistentRole(Model):
    guild_id: int
    user_id: int
    role_id: Optional[int]

    @classmethod
    async def list_by_guild(cls, guild_id: int, user_id: int):
        query = """SELECT * FROM persistent_roles WHERE guild_id = $1 and user_id = $2"""
        return await cls.fetch(query, guild_id, user_id)

    @classmethod
    async def insert_by_guild(cls, guild_id: int, user_id: int, role_id: int):
        query = """INSERT INTO persistent_roles (guild_id, user_id, role_id)
                        VALUES ($1, $2, $3)
                   ON CONFLICT (guild_id, user_id, role_id)
                   DO NOTHING"""

        await cls.execute(query, guild_id, user_id, role_id)

    @classmethod
    async def delete_by_guild(cls, guild_id: int, user_id: int):
        query = """DELETE FROM persistent_roles WHERE guild_id = $1 and user_id = $2"""
        return await cls.fetch(query, guild_id, user_id)
