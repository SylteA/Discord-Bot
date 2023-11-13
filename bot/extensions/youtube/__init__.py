from bot.core import DiscordBot

from .tasks import YoutubeTasks


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(YoutubeTasks(bot=bot))
