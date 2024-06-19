import asyncio
import datetime

import discord
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.chess.utils import lichess


class ChessTasks(commands.Cog):
    """Tasks for Chess functions"""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.medals = ["🥇", "🥈", "🥉"]
        self.time_controls = {
            "60+0": ("Blitz", "180+2", 5),
            "180+2": ("Rapid", "600+0", 5),
            "600+0": ("Bullet", "60+0", 7),
        }

    @property
    def channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.chess.channel_id)

    async def run_task(self, event: discord.ScheduledEvent):
        """Creates the chess tournament when it's time based on the event start time."""

        until = (event.start_time - datetime.timedelta(hours=1)).replace(tzinfo=None)
        if until > datetime.datetime.utcnow():
            await asyncio.sleep((until - datetime.datetime.utcnow()).total_seconds())
        else:
            return

        tournament = await lichess.get_team_tournament()
        time_control = self.time_controls.get(
            f"{tournament.clock.limit}+{tournament.clock.increment}", ("Blitz", "180+2", 5)
        )
        time = time_control[1].split("+")

        tournament = await lichess.create_tournament(
            f"Weekly {time_control[0]} Tournament",
            int(event.start_time.timestamp() * 1000),
            int(time[1]),
            int(time[0]),
            time_control[2],
        )

        await self.channel.send(
            f"<@&{settings.chess.role_id}> {time_control[0]} chess tourney in less than an hour! "
            "Click the link below to join!\n"
            f"**<https://lichess.org/swiss/{tournament.id}>**\n\n"
            "Prizes:\n"
            "🥇 2500 pancakes 🥞\n"
            "🥈 1000 pancakes 🥞\n"
            "🥉 500 pancakes 🥞",
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        await event.edit(
            name=f"Weekly {time_control[0]} Tournament",
            location=f"https://lichess.org/swiss/{tournament.id}",
        )

        await asyncio.sleep((event.start_time.replace(tzinfo=None) - datetime.datetime.utcnow()).total_seconds())
        while True:
            tournament = await lichess.get_tournament(tournament.id)
            if tournament.status == "finished":
                break

            await asyncio.sleep(10)

        players = await lichess.get_tournament_results(tournament.id)
        await self.channel.send(
            "The tournament has ended! See you next time!\n\n"
            "Winners:\n"
            + "\n".join(f"{self.medals[i]} **{player['username']}**" for i, player in enumerate(players[:3]))
            + "\n\n(If you are one of the winners, please let us know by verifying your lichess username.)"
        )
