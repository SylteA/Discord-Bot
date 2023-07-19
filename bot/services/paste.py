from pydantic import BaseModel

from bot.config import settings
from bot.services import http


class Document(BaseModel):
    key: str

    @property
    def url(self) -> str:
        return settings.hastebin.base_url + "/" + self.key


async def create(content: str) -> Document:
    """Creates a hastebin Document with the provided content."""
    async with http.session.post(settings.hastebin.base_url + "/documents", data=content) as response:
        response.raise_for_status()

        data = await response.json()
        return Document(**data)
