import asyncio
import datetime as dt
import logging
import traceback
from datetime import datetime

import aiohttp
import discord
import pytz
from bs4 import BeautifulSoup
from discord.ext import commands, tasks

from bot import core
from bot.config import settings
from bot.services import http, paste

log = logging.getLogger(__name__)

aoc_time = dt.time(hour=0, minute=0, second=1, tzinfo=pytz.timezone("EST"))
YEAR = datetime.now(tz=pytz.timezone("EST")).year


class AdventOfCodeTasks(commands.Cog):
    """Tasks for the Advent of Code cog."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.daily_puzzle.start()

    def cog_unload(self):
        self.daily_puzzle.cancel()

    @property
    def channel(self) -> discord.TextChannel:
        return self.bot.get_channel(settings.aoc.channel_id)

    @tasks.loop(time=aoc_time)
    async def daily_puzzle(self):
        """Post the daily Advent of Code puzzle"""

        day = datetime.now(tz=pytz.timezone("EST")).day
        month = datetime.now(tz=pytz.timezone("EST")).month
        if day > 25 or month != 12:
            return

        puzzle_url = f"https://adventofcode.com/{YEAR}/day/{day}"
        raw_html = None
        for retry in range(4):
            async with aiohttp.ClientSession(raise_for_status=False) as session:
                async with session.get(puzzle_url) as resp:
                    if resp.status == 200:
                        raw_html = await resp.text()
                        break
                await asyncio.sleep(10)

        if not raw_html:
            return await self.channel.send(
                f"<@&{settings.aoc.role_id}> Good morning! Day {day} is ready to be attempted."
                f"View it online now at {puzzle_url}. Good luck!",
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

        soup = BeautifulSoup(raw_html, "html.parser")
        article = soup.find("article", class_="day-desc")
        title = article.find("h2").text.replace("---", "").strip()
        desc = article.find("p").text.strip()

        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.red(),
            url=puzzle_url,
            timestamp=datetime.now(tz=pytz.timezone("EST")).replace(hour=0, minute=0, second=0, microsecond=0),
        )
        embed.set_author(
            name="Advent Of Code", url="https://adventofcode.com", icon_url="https://adventofcode.com/favicon.png"
        )

        await self.channel.send(
            f"<@&{settings.aoc.role_id}> Good morning! Day {day} is ready to be attempted.",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

    @daily_puzzle.error
    async def daily_puzzle_error(self, error: Exception):
        """Log any errors raised by the daily puzzle task"""

        content = "\n".join(traceback.format_exception(type(error), error, error.__traceback__))
        header = "Ignored exception in daily puzzle task"

        def wrap(code: str) -> str:
            code = code.replace("`", "\u200b`")
            return f"```py\n{code}\n```"

        if len(content) > 1024:
            document = await paste.create(content)
            content = wrap(content[:1024]) + f"\n\n [Full traceback]({document.url})"
        else:
            content = wrap(content)

        embed = discord.Embed(
            title=header, description=content, color=discord.Color.red(), timestamp=discord.utils.utcnow()
        )
        await discord.Webhook.from_url(url=settings.errors.webhook_url, session=http.session).send(embed=embed)

        log.error("Daily puzzle task failed", exc_info=error)
