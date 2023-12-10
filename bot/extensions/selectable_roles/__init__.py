from bot.core import DiscordBot

from .commands import SelectableRoleCommands


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(SelectableRoleCommands(bot=bot))
