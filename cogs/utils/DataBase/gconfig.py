from typing import List
from asyncio import Lock


class FilterConfig(object):
    def __init__(self, bot, guild_id: int, blacklist_urls: List[str],
                 whitelist_channels: List[int], enabled: bool = True):
        self.bot = bot
        self.guild_id = guild_id
        self.blacklist_urls = blacklist_urls
        self.whitelist_channels = whitelist_channels
        self.enabled = enabled
        self.update_lock = Lock(loop=self.bot.loop)

    async def post(self):
        query = """INSERT INTO gconfigs ( guild_id, blacklist_urls, whitelist_channels )
                   VALUES ( $1, $2, $3 )"""
        await self.bot.db.execute(query, self.guild_id, self.blacklist_urls, self.whitelist_channels)
        return self

    async def update(self):
        async with self.update_lock:
            query = """UPDATE gconfigs SET blacklist_urls = $1, whitelist_channels = $2, enabled = $3 
                       WHERE guild_id = $4"""
            await self.bot.db.execute(query, self.blacklist_urls, self.whitelist_channels, self.enabled, self.guild_id)

    async def toggle(self):
        async with self.update_lock:
            if self.enabled:
                self.enabled = False
            else:
                self.enabled = True
        await self.update()
