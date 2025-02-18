from bot.core import DiscordBot

from .commands import ClashOfCode


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(ClashOfCode(bot=bot))
