from bot.config import settings
from bot.core import DiscordBot

from .commands import ClashOfCode
from .utils import coc_client


async def setup(bot: DiscordBot) -> None:
    await coc_client.login(remember_me_cookie=settings.coc.session_cookie)
    await bot.add_cog(ClashOfCode(bot=bot))
