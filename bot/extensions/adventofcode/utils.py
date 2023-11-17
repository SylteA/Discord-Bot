from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import aiohttp
import discord
from pydantic import BaseModel, validator

from bot.config import settings

YEAR = datetime.now(tz=ZoneInfo("EST")).year
LEADERBOARD_ID = settings.aoc.leaderboard_id
LEADERBOARD_CODE = settings.aoc.leaderboard_code
API_URL = f"https://adventofcode.com/{YEAR}/leaderboard/private/view/{LEADERBOARD_ID}.json"
AOC_REQUEST_HEADER = {"user-agent": "Tech With Tim Discord Bot https://github.com/SylteA/Discord-Bot"}
AOC_SESSION_COOKIE = {"session": settings.aoc.session_cookie}


def home_embed():
    embed = discord.Embed(title="", colour=0x68C290)
    embed.set_author(
        name="Advent of Code",
        url="https://adventofcode.com",
        icon_url="https://adventofcode.com/favicon.png",
    )
    embed.add_field(
        name="Join the Leaderboard!",
        value="Head over to https://adventofcode.com/leaderboard/private"
        f" with the code `{LEADERBOARD_CODE}` to join the TWT private leaderboard!",
        inline=False,
    )

    puzzle_time = next_puzzle()
    if puzzle_time:
        embed.add_field(
            name="Next Puzzle",
            value=f"The next puzzle is {discord.utils.format_dt(puzzle_time, 'R')}",
            inline=False,
        )

    return embed


def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


def next_puzzle():
    now = datetime.now(tz=ZoneInfo("EST"))
    if now.month == 12:
        if now.day >= 25:
            return False

        # If it's December, calculate time until the next midnight EST time
        target = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        # If it's not December, calculate time until the first of December
        target = datetime(now.year, 12, 1, tzinfo=ZoneInfo("EST"))

    return target


class Member(BaseModel):
    global_score: int
    name: str
    stars: int
    last_star_ts: int
    completion_day_level: dict
    id: int
    local_score: int

    @validator("name", pre=True)
    def set_name_to_anonymous(cls, val: Optional[str]) -> str:
        if val is None:
            return "Anonymous User"
        return val


async def fetch_leaderboard(local: bool = False) -> str:
    url = f"https://adventofcode.com/{YEAR}/leaderboard"
    if local:
        url += f"/private/view/{LEADERBOARD_ID}.json"

    async with aiohttp.ClientSession(cookies=AOC_SESSION_COOKIE, headers=AOC_REQUEST_HEADER) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                response = await resp.text()
            else:
                resp.raise_for_status()

    return response
