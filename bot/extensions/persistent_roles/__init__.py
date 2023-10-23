from bot.core import DiscordBot

from .commands import PersistentRoles
from .events import PersistentEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(PersistentRoles(bot=bot))
    await bot.add_cog(PersistentEvents(bot=bot))
