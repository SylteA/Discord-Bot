from bot.core import DiscordBot

from .commands import ReadTheDocs


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(ReadTheDocs(bot=bot))
