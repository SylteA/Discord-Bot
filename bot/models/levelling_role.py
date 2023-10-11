from .model import Model


class LevellingRole(Model):
    guild_id: int
    role_id: int
    level: int

    @classmethod
    async def get(cls, guild_id: int):
        query = """SELECT guild_id, role_id, level FROM levelling_roles WHERE guild_id=$1"""
        return await cls.fetch(query, guild_id)
