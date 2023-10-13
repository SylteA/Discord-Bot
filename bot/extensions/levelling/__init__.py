from bot.core import DiscordBot

from .commands import Levelling
from .events import LevelEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Levelling(bot=bot))
    await bot.add_cog(LevelEvents(bot=bot))
