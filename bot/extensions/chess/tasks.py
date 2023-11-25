import asyncio
import datetime
import json

import discord
from discord.ext import commands, tasks

from bot import core
from bot.config import settings
from bot.services import http

CHESS_HEADERS = {"Authorization": f"Bearer {settings.chess.access_token}"}


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
        self.check_events.start()

    def cog_unload(self) -> None:
        self.check_events.cancel()

    @property
    def channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.chess.channel_id)

    @tasks.loop(minutes=2)
    async def check_events(self):
        """Checks for new events on the server"""

        for event in self.channel.guild.scheduled_events:
            if event.location != f"<#{self.channel.id}>":
                continue

            until = event.start_time.timestamp() - datetime.datetime.now().timestamp()
            if not (58 < until / 60 < 60):
                continue

            async with http.session.get(
                f"https://lichess.org/api/team/{settings.chess.team_id}/swiss",
                headers=CHESS_HEADERS,
                params={"max": 1},
                raise_for_status=True,
            ) as resp:
                try:
                    tournament = json.loads(await resp.content.read())
                except json.JSONDecodeError:
                    tournament = {"clock": {"limit": 60, "increment": 0}}

            time_control = self.time_controls.get(
                f'{tournament["clock"]["limit"]}+{tournament["clock"]["increment"]}', ("Blitz", "180+2", 5)
            )
            time = time_control[1].split("+")

            async with http.session.post(
                f"https://lichess.org/api/swiss/new/{settings.chess.team_id}",
                headers=CHESS_HEADERS,
                data={
                    "name": f"Weekly {time_control[0]} Tournament",
                    "clock.limit": time[0],
                    "clock.increment": time[1],
                    "nbRounds": time_control[2],
                    "startsAt": int(event.start_time.timestamp() * 1000),
                },
                raise_for_status=True,
            ) as resp:
                tournament = await resp.json()

            await self.channel.send(
                f"<@&{settings.chess.role_id}> {time_control[0]} chess tourney in less than an hour! "
                "Click the link below to join!\n"
                f"**<https://lichess.org/swiss/{tournament['id']}>**\n\n"
                "Prizes:\n"
                "🥇 2500 pancakes 🥞\n"
                "🥈 1000 pancakes 🥞\n"
                "🥉 500 pancakes 🥞",
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

            await asyncio.sleep(until)
            while True:
                async with http.session.get(
                    f"https://lichess.org/api/swiss/{tournament['id']}", headers=CHESS_HEADERS
                ) as resp:
                    tournament = await resp.json()

                if tournament["status"] == "finished":
                    break
                await asyncio.sleep(10)

            async with http.session.get(
                f"https://lichess.org/api/swiss/{tournament['id']}/results", headers=CHESS_HEADERS, params={"nb": 3}
            ) as resp:
                results = await resp.text()
                players = [json.loads(result) for result in results.split("\n") if result]

            await self.channel.send(
                "The tournament has ended! See you next time!\n\n"
                "Winners:\n"
                + "\n".join(f"{self.medals[i]} **{player['username']}**" for i, player in enumerate(players[:3]))
                + "\n\n(If you are one of the winners, please let us know by verifying your lichess username.)"
            )

    @check_events.error
    async def on_check_error(self, _error: Exception):
        """Logs any errors that occur during the check_events task"""
        await self.bot.on_error("check_chess_events")
