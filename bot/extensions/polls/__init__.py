from bot.core import DiscordBot

from .commands import Polls
from .events import PollEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Polls(bot=bot))
    await bot.add_cog(PollEvents(bot=bot))
