from .model import Model


class CustomRoles(Model):
    id: int
    role_id: int
    guild_id: int
    name: str
    color: str

    @classmethod
    async def insert_by_guild(cls, role_id: int, guild_id: int, name: str, color: str):
        query = """INSERT INTO custom_roles (role_id, guild_id, name, color)
                        VALUES($1, $2, $3, $4)"""
        await cls.execute(query, role_id, guild_id, name, color)

    @classmethod
    async def delete_by_guild(cls, guild_id: int, role_id: int):
        query = """DELETE FROM custom_roles WHERE guild_id = $1 and role_id = $2"""
        await cls.execute(query, guild_id, role_id)
