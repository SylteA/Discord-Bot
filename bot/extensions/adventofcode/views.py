import re
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from bs4 import BeautifulSoup
from discord import ui

from bot import core
from bot.extensions.adventofcode.utils import LEADERBOARD_ID, YEAR, Member, fetch_leaderboard, home_embed, ordinal


class CreateAdventOfCodeView(ui.View):
    HOME_CUSTOM_ID = "extensions:adventofcode:home"
    LOCAL_LEADERBOARD_CUSTOM_ID = "extensions:adventofcode:local"
    GLOBAL_LEADERBOARD_CUSTOM_ID = "extensions:adventofcode:global"

    def reset_buttons(self):
        self.children[0].disabled = True
        self.children[1].disabled = False
        self.children[2].disabled = False

    @discord.ui.button(label="Home", style=discord.ButtonStyle.gray, emoji="🏠", custom_id=HOME_CUSTOM_ID, disabled=True)
    async def home(self, interaction: core.InteractionType, _button: ui.Button):
        self.reset_buttons()
        await interaction.response.edit_message(embed=home_embed(), view=self)

    @discord.ui.button(
        label="Local Leaderboard", style=discord.ButtonStyle.gray, emoji="👥", custom_id=LOCAL_LEADERBOARD_CUSTOM_ID
    )
    async def local_leaderboard(self, interaction: core.InteractionType, button: ui.Button):
        leaderboard = await fetch_leaderboard(local=True)

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
        embed.set_footer(text=f"Current Day: {datetime.now(tz=ZoneInfo('EST')).day}/25")

        button.disabled = True
        self.children[0].disabled = False
        self.children[2].disabled = False

        await interaction.response.edit_message(embed=embed, view=self)
        self.reset_buttons()

    @discord.ui.button(
        label="Global Leaderboard", style=discord.ButtonStyle.gray, emoji="🌎", custom_id=GLOBAL_LEADERBOARD_CUSTOM_ID
    )
    async def global_leaderboard(self, interaction: core.InteractionType, button: ui.Button):
        raw_html = await fetch_leaderboard()
        soup = BeautifulSoup(raw_html, "html.parser")

        button.disabled = True
        self.children[0].disabled = False
        self.children[1].disabled = False

        embed = discord.Embed(
            title="Advent of Code Global Leaderboard",
            colour=0x68C290,
            url=f"https://adventofcode.com/{YEAR}/leaderboard",
        )

        if soup.find("p").text == "Nothing to show on the leaderboard... yet.":
            embed.description = "The global leaderboard is not available yet. Please try again later."
            await interaction.response.edit_message(embed=embed, view=self)
            return self.reset_buttons()

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
            f"`{index}` {lb_list[index - 1][2]} - {lb_list[index - 1][1]} "
            for index, title in enumerate(lb_list[:10], start=1)
        )

        embed.description = s_desc

        await interaction.response.edit_message(embed=embed, view=self)
        self.reset_buttons()
