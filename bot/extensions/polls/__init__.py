from bot.core import DiscordBot

from .commands import Polls
from .events import PollsEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Polls(bot=bot))
    await bot.add_cog(PollsEvents(bot=bot))
