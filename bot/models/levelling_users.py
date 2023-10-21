from typing import Optional

from .model import Model


class Levels(Model):
    id: int
    rank: Optional[int]
    guild_id: int
    user_id: int
    old_total_xp: Optional[int]
    total_xp: int

    @classmethod
    async def insert_by_guild(cls, guild_id: int, user_id: int, total_xp: int):
        query = """INSERT INTO levelling_users (guild_id, user_id, total_xp)
                        VALUES ($1, $2, $3)
                   ON CONFLICT (guild_id, user_id)
                     DO UPDATE
                           SET total_xp = levelling_users.total_xp + $3, last_msg = CURRENT_TIMESTAMP
                         WHERE levelling_users.guild_id = $1
                           AND levelling_users.user_id = $2
                   AND EXTRACT(EPOCH FROM (NOW() - levelling_users.last_msg)) > 60
                     RETURNING total_xp - $3 AS old_total_xp, total_xp, guild_id, user_id, id;
"""
        return await cls.fetchrow(query, guild_id, user_id, total_xp)

    @classmethod
    async def give_xp(cls, guild_id: int, user_id: int, total_xp: int):
        query = """INSERT INTO levelling_users (guild_id, user_id, total_xp)
                        VALUES ($1, $2, $3)
                    ON CONFLICT (guild_id, user_id)
                  DO UPDATE SET total_xp = levelling_users.total_xp + $3
                      RETURNING total_xp - $3 AS old_total_xp, total_xp, guild_id, user_id, id;
                   """

        return await cls.fetchrow(query, guild_id, user_id, total_xp)

    @classmethod
    async def remove_xp(cls, guild_id: int, user_id: int, total_xp: int):
        query = """INSERT INTO levelling_users (guild_id, user_id, total_xp)
                        VALUES ($1, $2, $3)
                   ON CONFLICT (guild_id, user_id)
                 DO UPDATE SET total_xp = levelling_users.total_xp - $3
                     RETURNING total_xp + $3 AS old_total_xp, total_xp, guild_id, user_id, id;
                   """

        return await cls.fetchrow(query, guild_id, user_id, total_xp)
