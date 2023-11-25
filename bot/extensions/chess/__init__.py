from bot.core import DiscordBot

from .tasks import ChessTasks


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(ChessTasks(bot=bot))
