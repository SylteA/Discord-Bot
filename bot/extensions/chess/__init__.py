from bot.core import DiscordBot

from .events import ChessEvents
from .tasks import ChessTasks


async def setup(bot: DiscordBot) -> None:
    await bot.add_cog(ChessTasks(bot=bot))
    await bot.add_cog(ChessEvents(bot=bot))
