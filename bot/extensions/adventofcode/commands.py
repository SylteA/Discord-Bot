import re
from datetime import datetime
from typing import Optional

import aiohttp
import discord
import pytz
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands
from pydantic import BaseModel, validator

from bot import core
from bot.config import settings

YEAR = datetime.now(tz=pytz.timezone("EST")).year

LEADERBOARD_ID = settings.aoc.leaderboard_id
LEADERBOARD_CODE = settings.aoc.leaderboard_code
API_URL = f"https://adventofcode.com/{YEAR}/leaderboard/private/view/{LEADERBOARD_ID}.json"
AOC_REQUEST_HEADER = {"user-agent": "Tech With Tim Discord Bot https://github.com/SylteA/Discord-Bot"}
AOC_SESSION_COOKIE = {"session": settings.aoc.session_cookie}


def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


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


class AdventOfCode(commands.GroupCog, group_name="aoc"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def role(self) -> discord.Role:
        return self.bot.get_role(settings.aoc.role_id)

    @app_commands.command()
    async def subscribe(self, interaction: core.InteractionType):
        """Subscribe to receive notifications for new puzzles"""

        if self.role not in interaction.user.roles:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(
                "Okay! You have been __subscribed__ to notifications about new Advent of Code tasks."
                "You can run `/aoc unsubscribe` to disable them again for you.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Hey, you already are receiving notifications about new Advent of Code tasks."
                "If you don't want them any more, run `/aoc unsubscribe` instead.",
                ephemeral=True,
            )

    @app_commands.command()
    async def unsubscribe(self, interaction: core.InteractionType):
        """Unsubscribe from receiving notifications for new puzzles"""

        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            await interaction.response.send_message(
                "Okay! You have been __unsubscribed__ from notifications about new Advent of Code tasks.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Hey, you don't even get any notifications about new Advent of Code tasks currently anyway.",
                ephemeral=True,
            )

    @app_commands.command()
    async def countdown(self, interaction: core.InteractionType):
        """Get the time left until the next puzzle is released"""

        if (
            int(datetime.now(tz=pytz.timezone("EST")).day) in range(1, 25)
            and int(datetime.now(tz=pytz.timezone("EST")).month) == 12
        ):
            days = 24 - int(datetime.now().strftime("%d"))
            hours = 23 - int(datetime.now().strftime("%H"))
            minutes = 59 - int(datetime.now().strftime("%M"))

            embed = discord.Embed(
                title="Advent of Code",
                description=f"There are {str(days)} days {str(hours)} hours "
                f"and {str(minutes)} minutes left until AOC gets over.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            await interaction.response.send_message("Advent of Code is not currently running.", ephemeral=True)

    @app_commands.command(name="join")
    async def join_leaderboard(self, interaction: core.InteractionType):
        """Learn how to join the leaderboard"""

        await interaction.response.send_message(
            "Head over to https://adventofcode.com/leaderboard/private"
            f"with the code `{LEADERBOARD_CODE}` to join the TWT private leaderboard!",
            ephemeral=True,
        )

    @app_commands.command()
    async def leaderboard(self, interaction: core.InteractionType):
        """Get a snapshot of the TWT private AoC leaderboard"""

        if interaction.channel_id != settings.aoc.channel_id:
            return await interaction.response.send_message(
                f"Please use the <#{settings.aoc.channel_id}> channel", ephemeral=True
            )

        async with aiohttp.ClientSession(cookies=AOC_SESSION_COOKIE, headers=AOC_REQUEST_HEADER) as session:
            async with session.get(API_URL) as resp:
                if resp.status == 200:
                    leaderboard = await resp.json()
                else:
                    resp.raise_for_status()

        members = [Member(**member_data) for member_data in leaderboard["members"].values()]

        embed = discord.Embed(
            title=f"{interaction.guild.name} Advent of Code Leaderboard",
            colour=0x68C290,
            url=f"https://adventofcode.com/{YEAR}/leaderboard/private/view/{LEADERBOARD_ID}",
        )

        leaderboard = {
            "owner_id": leaderboard["owner_id"],
            "event": leaderboard["event"],
            "members": members,
        }
        members = leaderboard["members"]

        for i, member in enumerate(sorted(members, key=lambda x: x.local_score, reverse=True)[:10], 1):
            embed.add_field(
                name=f"{ordinal(i)} Place: {member.name} ({member.stars} ⭐)",
                value=f"Local Score: {member.local_score} | Global Score: {member.global_score}",
                inline=False,
            )
        embed.set_footer(text=f"Current Day: {datetime.now(tz=pytz.timezone('EST')).day}/25")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="global")
    async def global_leaderboard(self, interaction: core.InteractionType, number_of_people_to_display: int = 10):
        """Get a snapshot of the global AoC leaderboard"""
        if interaction.channel_id != settings.aoc.channel_id:
            return await interaction.response.send_message(
                f"Please use the <#{settings.aoc.channel_id}> channel", ephemeral=True
            )

        aoc_url = f"https://adventofcode.com/{YEAR}/leaderboard"
        number_of_people_to_display = min(25, number_of_people_to_display)

        async with aiohttp.ClientSession(headers=AOC_REQUEST_HEADER) as session:
            async with session.get(aoc_url) as resp:
                if resp.status == 200:
                    raw_html = await resp.text()
                else:
                    resp.raise_for_status()

        soup = BeautifulSoup(raw_html, "html.parser")
        ele = soup.find_all("div", class_="leaderboard-entry")

        exp = r"(?:[ ]{,2}(\d+)\))?[ ]+(\d+)\s+([\w\(\)\#\@\-\d ]+)"

        lb_list = []
        for entry in ele:
            # Strip off the AoC++ decorator
            raw_str = entry.text.replace("(AoC++)", "").rstrip()

            # Group 1: Rank
            # Group 2: Global Score
            # Group 3: Member string
            r = re.match(exp, raw_str)

            rank = int(r.group(1)) if r.group(1) else None
            global_score = int(r.group(2))

            member = r.group(3)
            if member.lower().startswith("(anonymous"):
                # Normalize anonymous user string by stripping () and title casing
                member = re.sub(r"[\(\)]", "", member).title()

            lb_list.append((rank, global_score, member))

        s_desc = "\n".join(
            f"`{index}` {lb_list[index-1][2]} - {lb_list[index-1][1]} "
            for index, title in enumerate(lb_list[:number_of_people_to_display], start=1)
        )

        embed = discord.Embed(
            title="Advent of Code Global Leaderboard",
            colour=0x68C290,
            url="https://adventofcode.com",
            description=s_desc,
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AdventOfCode(bot))
