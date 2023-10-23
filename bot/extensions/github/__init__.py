from bot.core import DiscordBot

from .commands import GitHub


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(GitHub(bot=bot))
