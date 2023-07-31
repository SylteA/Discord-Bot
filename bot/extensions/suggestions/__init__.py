from bot.core import DiscordBot

from .commands import Suggestions


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Suggestions(bot=bot))
