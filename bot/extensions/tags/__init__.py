from bot.core import DiscordBot

from .commands import Tags
from .events import TagEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(Tags(bot=bot))
    await bot.add_cog(TagEvents(bot=bot))
