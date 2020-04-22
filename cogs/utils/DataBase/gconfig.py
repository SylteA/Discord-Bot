from typing import List, Union
from asyncio import Lock
from json import dumps, loads


class FilterConfig(object):
    def __init__(self, bot, guild_id: int, blacklist_urls: List[str],
                 whitelist_channels: List[int], reasons: dict = None, enabled: bool = True):
        self.bot = bot
        self.guild_id = guild_id
        self.blacklist_urls = blacklist_urls
        self.whitelist_channels = whitelist_channels
        self.reasons = loads(reasons) if reasons is not None else {}
        self.enabled = enabled
        self.update_lock = Lock(loop=self.bot.loop)

    async def post(self):
        query = """INSERT INTO gconfigs ( guild_id, blacklist_urls, whitelist_channels, reasons )
                   VALUES ( $1, $2, $3 )"""
        await self.bot.db.execute(query, self.guild_id, self.blacklist_urls,
                                  self.whitelist_channels, dumps(self.reasons))
        return self

    async def update(self) -> None:
        async with self.update_lock:
            query = """UPDATE gconfigs SET blacklist_urls = $1, whitelist_channels = $2, enabled = $3, reasons = $4
                       WHERE guild_id = $5"""
            await self.bot.db.execute(query, self.blacklist_urls, self.whitelist_channels,
                                      self.enabled, dumps(self.reasons), self.guild_id)

    async def toggle(self) -> None:
        """Toggle this instance of FilterConfig"""
        async with self.update_lock:
            if self.enabled:
                self.enabled = False
            else:
                self.enabled = True
        await self.update()

    def has_reason(self, key: str) -> Union[str, None]:
        """Check if the blacklisted url has a reason stored"""
        return self.reasons.get(key, None)
