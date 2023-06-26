from bot.core import DiscordBot

from .commands import ChallengeCommands
from .events import ChallengeEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(ChallengeCommands(bot=bot))
    await bot.add_cog(ChallengeEvents(bot=bot))
