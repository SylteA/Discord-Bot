import asyncio
import datetime as dt
from datetime import datetime

import aiohttp
import discord
import pytz
from discord.ext import commands, tasks

from bot import core
from bot.config import settings

aoc_time = dt.time(hour=0, minute=0, second=1, tzinfo=pytz.timezone("EST"))
YEAR = datetime.now(tz=pytz.timezone("EST")).year


class AdventOfCodeTasks(commands.Cog):
    """Tasks for the Advent of Code cog."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.daily_puzzle.start()

    def cog_unload(self) -> None:
        self.daily_puzzle.cancel()

    @property
    def channel(self) -> discord.TextChannel:
        return self.bot.get_channel(settings.aoc.channel_id)

    @tasks.loop(time=aoc_time)
    async def daily_puzzle(self) -> None:
        """Post the daily Advent of Code puzzle"""

        day = datetime.now(tz=pytz.timezone("EST")).day
        month = datetime.now(tz=pytz.timezone("EST")).month
        if day > 25 or month != 12:
            return

        puzzle_url = f"https://adventofcode.com/{YEAR}/day/{day}"
        # Check if the puzzle is already available
        for retry in range(4):
            async with aiohttp.ClientSession(raise_for_status=False) as session:
                async with session.get(puzzle_url) as resp:
                    if resp.status == 200:
                        break
                await asyncio.sleep(10)

        await self.channel.send(
            f"<@&{settings.aoc.role_id}> Good morning! Day {day} is ready to be attempted."
            f"View it online now at {puzzle_url}. Good luck!",
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
