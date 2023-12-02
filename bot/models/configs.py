from .model import Model


class Config(Model):
    id: int
    guild_id: int
    min_xp: int
    max_xp: int
    xp_boost: int
    custom_role_log_channel_id: int | None

    @classmethod
    async def ensure_exists(cls, guild_id: int):
        query = """
            INSERT INTO configs (guild_id)
                 VALUES ($1)
            ON CONFLICT (guild_id)
          DO UPDATE SET guild_id = configs.guild_id
              RETURNING *"""
        return await cls.fetchrow(query, guild_id)
