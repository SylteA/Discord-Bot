from bot.core import DiscordBot

from .commands import Levelling
from .events import LevellingEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Levelling(bot=bot))
    await bot.add_cog(LevellingEvents(bot=bot))
