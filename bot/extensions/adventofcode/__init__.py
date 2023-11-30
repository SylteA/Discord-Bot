from bot.core import DiscordBot

from .commands import AdventOfCode
from .tasks import AdventOfCodeTasks


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(AdventOfCode(bot=bot))
    await bot.add_cog(AdventOfCodeTasks(bot=bot))
