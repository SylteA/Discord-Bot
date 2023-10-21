from .model import Model


class LevellingRole(Model):
    id: int
    guild_id: int
    role_id: int
    level: int

    @classmethod
    async def list_by_guild(cls, guild_id: int):
        query = """SELECT * FROM levelling_roles WHERE guild_id=$1"""
        return await cls.fetch(query, guild_id)

    @classmethod
    async def insert_by_guild(cls, guild_id: int, role_id: int, level: int):
        query = """INSERT INTO levelling_roles (guild_id, role_id, level)
                        VALUES ($1, $2, $3)
                   ON CONFLICT (guild_id, role_id)
                    DO NOTHING"""
        await cls.execute(query, guild_id, role_id, level)

    @classmethod
    async def delete_by_guild(cls, guild_id: int, role_id: int):
        query = """DELETE FROM levelling_roles WHERE guild_id = $1 and role_id = $2"""
        await cls.execute(query, guild_id, role_id)
