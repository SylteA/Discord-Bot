from .model import Model


class IgnoredChannel(Model):
    guild_id: int
    channel_id: int

    @classmethod
    async def list_by_guild(cls, guild_id: int):
        query = """SELECT * FROM ignored_channels WHERE guild_id = $1"""
        return await cls.fetch(query, guild_id)

    @classmethod
    async def insert_by_guild(cls, guild_id: int, channel_id: int):
        query = """INSERT INTO ignored_channels (guild_id,channel_id) VALUES($1, $2)
                   ON CONFLICT (guild_id,channel_id) DO NOTHING
                     RETURNING guild_id, channel_id"""
        return await cls.fetch(query, guild_id, channel_id)

    @classmethod
    async def delete_by_guild(cls, guild_id: int, channel_id: int):
        query = """DELETE FROM ignored_channel WHERE guild_id= $1 and channel_id = $2"""
        return await cls.fetch(query, guild_id, channel_id)
