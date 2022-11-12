from json import dumps, loads
from typing import List, Optional, Union

from pydantic import validator

from .model import Model


class FilterConfig(Model):
    guild_id: int
    blacklist_urls: List[str]
    whitelist_channels: List[int]
    reasons: dict
    enabled: bool = True

    _validate_reasons = validator("reasons", pre=True)(lambda r: loads(r) if isinstance(r, str) else r)

    @classmethod
    async def fetch_config(cls, guild_id: int, create_if_no_exist=True) -> Optional["FilterConfig"]:
        query = """SELECT * FROM gconfigs WHERE guild_id = $1"""
        config = await cls.fetchrow(query, guild_id)
        if config is None and create_if_no_exist:
            config = cls(guild_id=guild_id, blacklist_urls=[], whitelist_channels=[], reasons={})
            await config.post()
        return config

    async def post(self):
        query = """INSERT INTO gconfigs ( guild_id, blacklist_urls, whitelist_channels, reasons, enabled )
                   VALUES ( $1, $2, $3, $4, $5 )"""
        await self.execute(
            query, self.guild_id, self.blacklist_urls, self.whitelist_channels, dumps(self.reasons), self.enabled
        )

    async def update(self) -> None:
        query = """UPDATE gconfigs SET blacklist_urls = $1, whitelist_channels = $2, enabled = $3, reasons = $4
                   WHERE guild_id = $5"""
        await self.execute(
            query,
            self.blacklist_urls,
            self.whitelist_channels,
            self.enabled,
            dumps(self.reasons),
            self.guild_id,
        )

    async def toggle(self) -> None:
        """Toggle this instance of FilterConfig"""
        self.enabled = not self.enabled
        await self.update()

    def has_reason(self, key: str) -> Union[str, None]:
        """Check if the blacklisted url has a reason stored"""
        return self.reasons.get(key, None)
