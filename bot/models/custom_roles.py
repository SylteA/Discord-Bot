from .model import Model


class CustomRole(Model):
    id: int
    user_id: int | None
    guild_id: int
    role_id: int
    name: str
    color: int

    @classmethod
    async def ensure_exists(cls, guild_id: int, role_id: int, name: str, color: int, user_id: int = None):
        """Inserts or updates the custom role."""
        query = """
            INSERT INTO custom_roles (guild_id, role_id, name, color, user_id)
                 VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (guild_id, role_id)
              DO UPDATE SET
                   name = $3,
                  color = $4
             RETURNING *
        """

        return await cls.fetchrow(query, guild_id, role_id, name, color, user_id)
