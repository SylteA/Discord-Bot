import asyncio
import re
import time

import aiohttp
import discord
from discord import Forbidden, HTTPException, NotFound, app_commands
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.clashofcode.utils import coc_helper

REGEX = re.compile(r"https://www.codingame.com/clashofcode/clash/([0-9a-f]{39})")
API_URL = "https://www.codingame.com/services/ClashOfCode/findClashByHandle"


def em(mode, players):
    embed = discord.Embed(title="**Clash started**")
    embed.add_field(name="Mode", value=mode, inline=False)
    embed.add_field(name="Players", value=players)
    return embed


class ClashOfCode(commands.GroupCog, group_name="coc"):
    session_commands = app_commands.Group(
        name="session",
        description="Commands for clash of code sessions",
    )

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.session = False
        self.last_clash: int = 0

    @property
    def role(self):
        return self.bot.guild.get_role(settings.coc.role_id)

    @session_commands.command(name="start")
    async def session_start(self, interaction: core.InteractionType):
        """Start a new coc session"""

        if coc_helper.session_message != 0:
            return await interaction.response.send_message(
                "There is an active session right now.\n"
                "Join by reacting to the pinned message or using `/coc session join`. Have fun!",
                ephemeral=True,
            )

        pager = commands.Paginator(
            prefix=f"**Hey, {interaction.user.mention} is starting a coc session.\n"
            f"Use `/coc session join` or react to this message to join**",
            suffix="",
        )

        for member in self.role.members:
            if member != interaction.user:
                if member.status != discord.Status.offline:
                    pager.add_line(member.mention + ", ")

        if not len(pager.pages):
            return await interaction.response.send_message(
                "Nobody is online to play with <:pepesad:733816214010331197>", ephemeral=True
            )

        self.session = True
        self.last_clash = int(time.time())
        coc_helper.session_users.append(interaction.user.id)

        await interaction.response.send_message(pager.pages[0], allowed_mentions=discord.AllowedMentions(users=True))
        message = await interaction.original_response()
        coc_helper.session_message = message.id
        await message.add_reaction("🖐️")

        try:
            await message.pin()
        except (Forbidden, HTTPException):
            await interaction.channel.send("Failed to pin message")

        while coc_helper.session_message != 0:
            await asyncio.sleep(10)

            if self.last_clash + 1800 < int(time.time()) and coc_helper.session_message != 0:
                await interaction.channel.send("Clash session has been closed due to inactivity")
                try:
                    await message.unpin()
                except (Forbidden, HTTPException, NotFound):
                    await interaction.channel.send("Failed to unpin message")

                self.last_clash = 0
                coc_helper.session_users = []
                coc_helper.session_message = 0
                self.session = False
                break

    @session_commands.command(name="join")
    async def session_join(self, interaction: core.InteractionType):
        """Join the current active coc session"""

        if coc_helper.session_message == 0:
            return await interaction.response.send_message(
                "There is no active coc session right now" "use `/coc session start` to start a coc session",
                ephemeral=True,
            )

        if interaction.user.id in coc_helper.session_users:
            return await interaction.response.send_message(
                "You are already in the session. Have fun playing.\n"
                "If you want to leave remove your reaction or use `/coc session leave`",
                ephemeral=True,
            )

        coc_helper.session_users.append(interaction.user.id)
        return await interaction.response.send_message("You have joined the session. Have fun playing", ephemeral=True)

    @session_commands.command(name="leave")
    async def session_leave(self, interaction: core.InteractionType):
        """Leave the current active coc session"""

        if coc_helper.session_message == 0:
            return await interaction.response.send_message(
                "There is no active coc session right now" "use `/coc session start` to start a coc session",
                ephemeral=True,
            )

        if interaction.user.id not in coc_helper.session_users:
            return await interaction.response.send_message(
                "You aren't in a clash of code session right now.\n"
                "If you want to join react to session message or use `/coc session join`",
                ephemeral=True,
            )

        coc_helper.session_users.remove(interaction.user.id)
        return await interaction.response.send_message(
            "You have left the session. No more pings for now", ephemeral=True
        )

    @session_commands.command(name="end")
    async def session_end(self, interaction: core.InteractionType):
        """Ends the current coc session"""

        if coc_helper.session_message == 0:
            return await interaction.response.send_message("There is no active clash of code session", ephemeral=True)

        try:
            msg = await interaction.channel.fetch_message(coc_helper.session_message)
            try:
                await msg.unpin()
            except (Forbidden, HTTPException, NotFound):
                await interaction.channel.send("Failed to unpin message")
        except (Forbidden, HTTPException, NotFound):
            await interaction.channel.send("Error while fetching message to unpin")

        self.last_clash = 0
        coc_helper.session_users = []
        coc_helper.session_message = 0
        self.session = False

        return await interaction.response.send_message(
            f"Clash session has been closed by {interaction.user.mention}. See you later",
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    @app_commands.command(name="invite")
    async def coc_invite(self, interaction: core.InteractionType, url: str):
        """Mentions all the users with the `Clash Of Code` role that are in the current session."""

        if coc_helper.session_message == 0:
            return await interaction.response.send_message(
                "No active Clash of Code session please create one to start playing\n"
                "Use `/coc session start` to start a coc session <:smilecat:727592135171244103>",
                ephemeral=True,
            )

        if interaction.user.id not in coc_helper.session_users:
            return await interaction.response.send_message(
                "You can't create a clash unless you participate in the session\n"
                "Use `/coc session join` or react to the pinned message to join the coc session "
                "<:smilecat:727592135171244103>",
                ephemeral=True,
            )

        link = REGEX.fullmatch(url)
        if not link:
            return await interaction.response.send_message('Could not find any valid "clashofcode" url', ephemeral=True)

        # Defer the response to acknowledge the interaction while doing slow tasks
        await interaction.response.defer(ephemeral=True, thinking=True)

        self.last_clash = time.time()
        session_id = link[1]

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=[session_id]) as resp:
                json = await resp.json()

        plang = json["programmingLanguages"]
        pager = commands.Paginator(
            prefix="\n".join(
                [
                    f"**Hey, {interaction.user.mention} is hosting a Clash Of Code game!**",
                    f"Mode{'s' if len(json['modes']) > 1 else ''}: {', '.join(json['modes'])}",
                    f"Programming languages: {', '.join(plang) if plang else 'All'}",
                    f"Join here: {link[0]}",
                ]
            ),
            suffix="",
        )

        for member_id in coc_helper.session_users:
            if member_id != interaction.user.id:
                member = self.bot.get_user(member_id)
                pager.add_line(member.mention + ", ")

        if not len(pager.pages):
            return await interaction.followup.send(
                "Nobody is online to play with <:pepesad:733816214010331197>", ephemeral=True
            )

        for page in pager.pages:
            await interaction.channel.send(page, allowed_mentions=discord.AllowedMentions(users=True))

        await interaction.delete_original_response()

        async with aiohttp.ClientSession() as session:
            while not json["started"]:
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(API_URL, json=[session_id]) as resp:
                    json = await resp.json()

        players = len(json["players"])
        players_text = ", ".join(
            [p["codingamerNickname"] for p in sorted(json["players"], key=lambda p: p["position"])]
        )
        start_message = await interaction.channel.send(embed=em(json["mode"], players_text))

        async with aiohttp.ClientSession() as session:
            while not json["finished"]:
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(API_URL, json=[session_id]) as resp:
                    json = await resp.json()

                if len(json["players"]) != players:
                    players_text = ", ".join(
                        [p["codingamerNickname"] for p in sorted(json["players"], key=lambda p: p["position"])]
                    )
                    await start_message.edit(embed=em(json["mode"], players_text))

        embed = discord.Embed(
            title="**Clash finished**",
            description="\n".join(
                ["Results:"]
                + [
                    # Example "1. Takos (Code length: 123, Score 100%, Time 1:09)"
                    f"{p['rank']}. {p['codingamerNickname']} ("
                    + (f"Code length: {p['criterion']}, " if json["mode"] == "SHORTEST" else "")
                    + f"Score: {p['score']}%, Time: {p['duration'] // 60_000}:{p['duration'] // 1000 % 60:02})"
                    for p in sorted(json["players"], key=lambda p: p["rank"])
                ]
            ),
        )

        await interaction.channel.send(embed=embed)

    async def interaction_check(self, interaction: core.InteractionType):
        if interaction.channel_id != settings.coc.channel_id:
            await interaction.response.send_message(
                "You need to be in the Clash Of Code channel to use this command", ephemeral=True
            )
            return False

        if not any(
            role.id in (settings.moderation.staff_role_id, settings.coc.role_id) for role in interaction.user.roles
        ):
            await interaction.response.send_message(
                "You need to have the Clash Of Code role to use this command", ephemeral=True
            )
            return False

        return True


async def setup(bot: core.DiscordBot):
    await bot.add_cog(ClashOfCode(bot=bot))
