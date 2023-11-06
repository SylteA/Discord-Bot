from bot.core import DiscordBot

from .commands import YoutubeCommands
from .tasks import YoutubeTasks


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(YoutubeCommands(bot=bot))
    await bot.add_cog(YoutubeTasks(bot=bot))
