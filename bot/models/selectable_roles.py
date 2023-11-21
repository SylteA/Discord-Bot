from .model import Model


class SelectableRole(Model):
    guild_id: int
    role_id: int
    role_name: str

    @classmethod
    async def ensure_exists(cls, guild_id: int, role_id: int, role_name: str):
        """Inserts or updates the selectable role."""
        query = """
            INSERT INTO selectable_roles (guild_id, role_id, role_name)
                 VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, role_id)
                DO UPDATE SET
                     role_name = $3
        """

        return await cls.fetchrow(query, guild_id, role_id, role_name)
