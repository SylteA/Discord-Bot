from bot.core import DiscordBot

from .commands import CustomRoles
from .events import CustomRoleEvents


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(CustomRoles(bot=bot))
    await bot.add_cog(CustomRoleEvents(bot=bot))
