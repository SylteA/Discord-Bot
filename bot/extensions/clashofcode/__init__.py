from bot.core import DiscordBot

from .commands import ClashOfCode
from .events import ClashOfCodeEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(ClashOfCode(bot=bot))
    await bot.add_cog(ClashOfCodeEvents(bot=bot))
