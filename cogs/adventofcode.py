import asyncio
import logging
import datetime
import aiohttp
import pytz
import re
import inflect

from bs4 import BeautifulSoup
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from config import AOC_SESSION_COOKIE

log = logging.getLogger(__name__)
loop = asyncio.get_event_loop()

API_URL = "https://adventofcode.com/2021/leaderboard/private/view/975452.json"
AOC_CHANNEL = 782573489772953600
INTERVAL = 120
AOC_REQUEST_HEADER = {"user-agent": "TWT AoC Event Bot"}
AOC_SESSION_COOKIE = {"session": AOC_SESSION_COOKIE}
ENGINE = inflect.engine()
AOC_ROLE = int(782842606761148417)


def time_left_to_aoc_midnight():
    """Calculates the amount of time left until midnight in UTC-5 (Advent of Code maintainer timezone)."""
    # Change all time properties back to 00:00
    todays_midnight = datetime.now(tz=pytz.timezone("EST")).replace(
        microsecond=0, second=0, minute=0, hour=0
    )

    # We want tomorrow so add a day on
    tomorrow = todays_midnight + timedelta(days=1)

    # Calculate the timedelta between the current time and midnight
    return tomorrow, tomorrow - datetime.now(tz=pytz.timezone("UTC"))


async def day_countdown(bot: commands.Bot) -> None:
    """
    Calculate the number of seconds left until the next day of Advent.
    Once we have calculated this we should then sleep that number and when the time is reached, ping
    the Advent of Code role notifying them that the new challenge is ready.
    """
    while (
        int(datetime.now(tz=pytz.timezone("EST")).day) in range(1, 25)
        and int(datetime.now(tz=pytz.timezone("EST")).month) == 12
    ):
        tomorrow, time_left = time_left_to_aoc_midnight()

        # Prevent bot from being slightly too early in trying to announce today's puzzle
        await asyncio.sleep(time_left.seconds + 1)

        channel = bot.get_channel(AOC_CHANNEL)

        if not channel:
            break

        aoc_role = channel.guild.get_role(AOC_ROLE)
        if not aoc_role:
            break

        puzzle_url = f"https://adventofcode.com/2021/day/{tomorrow.day}"

        # Check if the puzzle is already available to prevent our members from spamming
        # the puzzle page before it's available by making a small HEAD request.
        for retry in range(1, 5):
            async with bot.session.head(puzzle_url, raise_for_status=False) as resp:
                if resp.status == 200:
                    break
            await asyncio.sleep(10)
        else:
            break

        await channel.send(
            f"{aoc_role.mention} Good morning! Day {tomorrow.day} is ready to be attempted. "
            f"View it online now at {puzzle_url}. Good luck!",
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                users=False,
                roles=[discord.Object(AOC_ROLE)],
            ),
        )


class Member:
    def __init__(self, results):
        self.global_score = results["global_score"]
        self.name = results["name"]
        self.stars = results["stars"]
        self.last_star_ts = results["last_star_ts"]
        self.completion_day_level = results["completion_day_level"]
        self.id = results["id"]
        self.local_score = results["local_score"]


class AdventOfCode(commands.Cog, name="Advent of Code"):
    def __init__(self, bot):
        self.bot = bot

        self._base_url = f"https://adventofcode.com/2021"
        self.global_leaderboard_url = f"https://adventofcode.com/2021/leaderboard"
        self.private_leaderboard_url = (
            f"{self._base_url}/leaderboard/private/view/975452"
        )

        countdown_coro = day_countdown(self.bot)
        self.countdown_task = loop.create_task(countdown_coro)

    @commands.group(name="adventofcode", aliases=("aoc",))
    async def adventofcode_group(self, ctx: commands.Context) -> None:
        """All of the Advent of Code commands."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @adventofcode_group.command(
        name="subscribe",
        aliases=("sub", "notifications", "notify", "notifs"),
        brief="Notifications for new days",
    )
    async def aoc_subscribe(self, ctx: commands.Context) -> None:
        """Assign the role for notifications about new days being ready."""
        role = ctx.guild.get_role(AOC_ROLE)
        unsubscribe_command = f"{ctx.prefix}{ctx.command.root_parent} unsubscribe"

        if role not in ctx.author.roles:
            await ctx.author.add_roles(role)
            await ctx.send(
                "Okay! You have been __subscribed__ to notifications about new Advent of Code tasks. "
                f"You can run `{unsubscribe_command}` to disable them again for you."
            )
        else:
            await ctx.send(
                "Hey, you already are receiving notifications about new Advent of Code tasks. "
                f"If you don't want them any more, run `{unsubscribe_command}` instead."
            )

    @adventofcode_group.command(
        name="unsubscribe", aliases=("unsub",), brief="Notifications for new days"
    )
    async def aoc_unsubscribe(self, ctx: commands.Context) -> None:
        """Remove the role for notifications about new days being ready."""
        role = ctx.guild.get_role(AOC_ROLE)

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(
                "Okay! You have been __unsubscribed__ from notifications about new Advent of Code tasks."
            )
        else:
            await ctx.send(
                "Hey, you don't even get any notifications about new Advent of Code tasks currently anyway."
            )

    @adventofcode_group.command(
        name="countdown",
        aliases=("count", "c"),
        brief="Return time left until Aoc Finishes",
    )
    async def aoc_countdown(self, ctx: commands.Context) -> None:
        """Return time left until Aoc Finishes."""
        if (
            int(datetime.now(tz=pytz.timezone("EST")).day) in range(1, 25)
            and int(datetime.now(tz=pytz.timezone("EST")).month) == 12
        ):
            days = 24 - int(datetime.now().strftime("%d"))
            hours = 23 - int(datetime.now().strftime("%H"))
            minutes = 59 - int(datetime.now().strftime("%M"))

            embed = discord.Embed(
                title="Advent of Code",
                description=f"There are {str(days)} days {str(hours)} hours and {str(minutes)} minutes left until AOC gets over.",
            )
            embed.set_footer(
                text=ctx.author.display_name, icon_url=ctx.author.avatar_url
            )
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"Aoc Hasn't Started Yet!")

    @adventofcode_group.command(
        name="join", aliases=("j",), brief="Learn how to join the leaderboard (via DM)"
    )
    async def join_leaderboard(self, ctx: commands.Context) -> None:
        """DM the user the information for joining the TWT AoC private leaderboard."""
        author = ctx.message.author

        info_str = (
            "Head over to https://adventofcode.com/leaderboard/private "
            f"with code `975452-d90a48b0` to join the TWT private leaderboard!"
        )
        try:
            await author.send(info_str)
        except discord.errors.Forbidden:
            await ctx.send(
                f":x: {author.mention}, please (temporarily) enable DMs to receive the join code"
            )
        else:
            await ctx.message.add_reaction("\U0001F4E8")

    @adventofcode_group.command(
        name="leaderboard",
        aliases=("board", "aoc_lb"),
        brief="Get a snapshot of the TWT private AoC leaderboard",
    )
    async def aoc_leaderboard(self, ctx: commands.Context):
        api_url = API_URL

        async with aiohttp.ClientSession(
            cookies=AOC_SESSION_COOKIE, headers=AOC_REQUEST_HEADER
        ) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    leaderboard = await resp.json()
                else:
                    resp.raise_for_status()

        members = [Member(leaderboard["members"][id]) for id in leaderboard["members"]]

        embed = discord.Embed(
            title=f"{ctx.guild.name} Advent of Code Leaderboard",
            colour=discord.Colour(0x68C290),
            url="https://adventofcode.com",
        )

        leaderboard = {
            "owner_id": leaderboard["owner_id"],
            "event": leaderboard["event"],
            "members": members,
        }
        members = leaderboard["members"]

        for member in members[:10]:
            place = members.index(member) + 1
            embed.add_field(
                name=f"{ENGINE.ordinal(place)} Place: {member.name} ({member.stars} :star:)",
                value=f"Local Score: {member.local_score} | Global Score: {member.global_score}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @adventofcode_group.command(
        name="global",
        aliases=("globalboard", "gb"),
        brief="Get a snapshot of the global AoC leaderboard",
    )
    async def global_leaderboard(
        self, ctx: commands.Context, number_of_people_to_display: int = 10
    ):
        aoc_url = f"https://adventofcode.com/2021/leaderboard"
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
            for index, title in enumerate(
                lb_list[:number_of_people_to_display], start=1
            )
        )

        embed = discord.Embed(
            title=f"Advent of Code Global Leaderboard",
            colour=discord.Colour(0x68C290),
            url="https://adventofcode.com",
            description=s_desc,
        )
        await ctx.send(embed=embed)

    @adventofcode_group.command(
        name="info",
        hidden=True,
        aliases=["about", "help", "faq"],
        brief="Learn about Advent of Code",
    )
    async def aoc_help(self, ctx):
        if not ctx.channel.id == AOC_CHANNEL:
            return

        text = """
        **Introduction**
        Advent of Code is a series of small programming puzzles for a variety of skill sets and skill levels in any programming language you like. An event where 25 programming puzzles are scattered over 25 days in December. It's a great opportunity to flex your puzzle/problem solving muscles, and perhaps even learn a new programming language if you feel adventurous! Overall, the difficulty of the challenges does increase as we get further into the event. 
        Every day at `00:00 EST (05:00 UTC)` a new puzzle is released.

        **Leaderboards**
        There is a [global leaderboard](https://adventofcode.com/2021/leaderboard) which will reward the first person to solve a given puzzle part with 100 points. The second fastest will get 99 and so on.

        **How to Participate**
        To participate, head on over to https://adventofcode.com/ and login.

        • Subscribe to reminders about Advent of Code with the command t.aoc subscribe.
        • Join the Tech With Tim leaderboard with the command t.aoc join. 
        • View the [Community leaderboard](https://adventofcode.com/2021/leaderboard/private/view/975452)with the command t.aoc leaderboard."""

        embed = discord.Embed(title="Advent of Code", description=text)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AdventOfCode(bot))
