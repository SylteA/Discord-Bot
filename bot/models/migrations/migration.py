import re
from datetime import datetime
from typing import Literal, Optional

from bot.models import Model


class Migration(Model):
    id: int = 0  # serial
    version: int
    direction: Literal["up", "down"]
    name: str
    timestamp: datetime | None  # it will be None if the migration hasn't been applied yet

    @property
    def filename(self):
        return f"{self.version:03}_{self.direction}__{self.name}.sql"

    @classmethod
    def from_match(cls, match: re.Match) -> "Migration":
        return cls(version=int(match.group("version")), direction=match.group("direction"), name=match.group("name"))

    @classmethod
    async def fetch_latest(cls) -> Optional["Migration"]:
        query = """SELECT * FROM migrations ORDER BY timestamp DESC LIMIT 1"""
        return await cls.fetchrow(query)

    async def post(self):
        query = """
        INSERT INTO migrations (version, direction, name, timestamp)
            VALUES ($1, $2, $3, $4)
        """
        await self.execute(query, self.version, self.direction, self.name, self.timestamp)
