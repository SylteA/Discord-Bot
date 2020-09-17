from discord.ext import commands
import discord

import aiohttp
import asyncio
import re

import time

coc_role = 729342805855567934
coc_channel = 729352136588263456
coc_message = 729355074085584918
REGEX = re.compile(r"https://www.codingame.com/clashofcode/clash/([0-9a-f]{39})")
API_URL = "https://www.codingame.com/services/ClashOfCode/findClashByHandle"


def setup(bot: commands.Bot):
    bot.add_cog(ClashOfCode(bot=bot))


class ClashOfCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = False
        self.session_message: int = 0
        self.session_users = []
        self.last_clash: int = 0

    @property
    def role(self):
        return self.bot.guild.get_role(coc_role)

    def em(self, mode, players):
        embed = discord.Embed(title="**Clash started**")
        embed.add_field(name="Mode", value=mode, inline=False)
        embed.add_field(name="Players", value=players)
        return embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if self.session_message != 0:
            if payload.message_id == self.session_message:
                if str(payload.emoji) == "🖐️":
                    if payload.user_id not in self.session_users:
                        self.session_users.append(payload.user_id)

        if payload.message_id != coc_message:
            return

        if self.role in payload.member.roles:
            return

        await payload.member.add_roles(self.role)
        try:
            await payload.member.send(f"Gave you the **{self.role.name}** role!")
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if self.session_message != 0:
            if payload.message_id == self.session_message:
                if str(payload.emoji) == "🖐️":
                    if payload.user_id in self.session_users:
                        self.session_users.remove(payload.user_id)

        if payload.message_id != coc_message:
            return

        member = self.bot.guild.get_member(payload.user_id)
        if self.role not in member.roles:
            return

        await member.remove_roles(self.role)
        try:
            await member.send(f"Removed your **{self.role.name}** role!")
        except discord.HTTPException:
            pass

    @commands.group(aliases=["coc"])
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    async def clash_of_code(self, ctx: commands.Context):
        """Clash of Code"""
        if ctx.invoked_subcommand is None:
            if self.session_message == 0:
                return await ctx.send_help(self.bot.get_command("coc session"))
            return await ctx.send_help(self.bot.get_command("coc invite"))

    @clash_of_code.group(aliases=['s'])
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    async def session(self, ctx: commands.Context):
        """ Start or End a clash of code session """
        if ctx.invoked_subcommand is None:
            if self.session_message == 0:
                return await ctx.send_help(self.bot.get_command("coc session start"))
            return await ctx.send_help(self.bot.get_command("coc session end"))

    @session.command(name="start", aliases=["s"])
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    async def session_start(self, ctx: commands.context):
        """ Start a new coc session """
        if self.session_message != 0:
            return await ctx.send("There is an active session right now.\n"
                                  "Join by reacting to the pinned message or using `t.coc session join`. Have fun!")

        pager = commands.Paginator(prefix=f"**Hey, {ctx.author.mention} is starting a coc session.\n"
                                          f"Use `t.coc session join` or react to this message to join**", suffix="")

        for member in self.role.members:
            if member != ctx.author:
                if member.status != discord.Status.offline:
                    pager.add_line(member.mention + ", ")

        if not len(pager.pages):
            return await ctx.send(f"{ctx.author.mention}, Nobody is online to play with <:pepesad:733816214010331197>")

        self.session = True
        self.last_clash = int(time.time())
        self.session_users.append(ctx.author.id)

        msg = await ctx.send(pager.pages[0])
        self.session_message = msg.id
        await msg.add_reaction("🖐️")

        try:
            await msg.pin()
        except:
            await ctx.send("Failed to pin message")

        while self.session_message != 0:
            await asyncio.sleep(10)

            if self.last_clash + 1800 < int(time.time()) and self.session_message != 0:
                await ctx.send("Clash session has been closed due to inactivity")
                try:
                    await msg.unpin()
                except:
                    await ctx.send("Failed to unpin message")

                self.last_clash = 0
                self.session_users = []
                self.session_message = 0
                self.session = False
                break

    @session.command(name='join', aliases=['j'])
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    async def session_join(self, ctx: commands.Context):
        """Join the current active coc session"""
        if self.session_message == 0:
            return await ctx.send("There is no active coc session right now"
                                  "use `t.coc session start` to start a coc session")
        if ctx.author.id in self.session_users:
            return await ctx.send("You are already in the session. Have fun playing.\n"
                                  "If you want to leave remove your reaction or use `t.coc session leave`")
        self.session_users.append(ctx.author.id)
        return await ctx.send("You have joined the session. Have fun playing")

    @session.command(name='leave', aliases=['l'])
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    async def session_leave(self, ctx: commands.Context):
        """Leave the current active coc session"""
        if self.session_message == 0:
            return await ctx.send("There is no active coc session right now"
                                  "use `t.coc session start` to start a coc session")
        if ctx.author.id not in self.session_users:
            return await ctx.send("You aren't in a clash of code session right now.\n"
                                  "If you want to join react to session message or use `t.coc session join`")
        self.session_users.remove(ctx.author.id)
        return await ctx.send("You have left the session. No more pings for now")

    @session.command(name="end", aliases=["e"])
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    async def session_end(self, ctx: commands.context):
        """ Ends the current coc session """
        if self.session_message == 0:
            return await ctx.send("There is no active clash of code session")

        try:
            msg = await ctx.channel.fetch_message(self.session_message)
            try:
                await msg.unpin()
            except:
                await ctx.send("Failed to unpin message")
        except:
            await ctx.send("Error while fetching message to unpin")

        self.last_clash = 0
        self.session_users = []
        self.session_message = 0
        self.session = False

        return await ctx.send(f"Clash session has been closed by {ctx.author.mention}. See you later")

    @clash_of_code.command(name="invite", aliases=["i"])
    @commands.has_any_role(
        511334601977888798,  # Tim
        580911082290282506,  # Admin
        511332506780434438,  # Mod
        541272748161499147,  # Helper
        coc_role
    )
    @commands.check(lambda ctx: ctx.channel.id == coc_channel)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def coc_invite(self, ctx: commands.Context, *, url: str=None):
        """Mentions all the users with the `Clash Of Code` role that are in the current session."""
        await ctx.message.delete()
        if self.session_message == 0:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("No active Clash of Code session please create one to start playing\n"
                                  "Use `t.coc session start` to start a coc session <:smilecat:727592135171244103>")

        if ctx.author.id not in self.session_users:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't create a clash unless you participate in the session\n"
                                  "Use `t.coc session join` or react to the pinned message to join the coc session "
                                  "<:smilecat:727592135171244103>")

        if url is None:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You should provide a valid clash of code url")

        link = REGEX.fullmatch(url)
        if not link:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send('Could not find any valid "clashofcode" url')

        self.last_clash = time.time()

        id = link[1]

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=[id]) as resp:
                json = await resp.json()

        pager = commands.Paginator(
            prefix="\n".join([
                f"**Hey, {ctx.author.mention} is hosting a Clash Of Code game!**",
                f"Mode{'s' if len(json['modes']) > 1 else ''}: {', '.join(json['modes'])}",
                f"Programming languages: {', '.join(json['programmingLanguages']) if json['programmingLanguages'] else 'All'}",
                f"Join here: {link[0]}"
            ]),
            suffix="",
        )

        for member_id in self.session_users:
            if member_id != ctx.author.id:
                member = self.bot.get_user(member_id)
                pager.add_line(member.mention + ", ")

        if not len(pager.pages):
            return await ctx.send(f"{ctx.author.mention}, Nobody is online to play with <:pepesad:733816214010331197>")

        for page in pager.pages:
            await ctx.send(page)

        async with aiohttp.ClientSession() as session:
            while not json["started"]:
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(API_URL, json=[id]) as resp:
                    json = await resp.json()

        players = len(json["players"])
        players_text = ', '.join([p['codingamerNickname']for p in sorted(json['players'], key=lambda p: p['position'])])
        start_message = await ctx.send(embed=self.em(json['mode'], players_text))

        async with aiohttp.ClientSession() as session:
            while not json["finished"]:
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(API_URL, json=[id]) as resp:
                    json = await resp.json()

                if len(json["players"]) != players:
                    players_text = ', '.join([p['codingamerNickname']
                                              for p in sorted(json['players'], key=lambda p: p['position'])])
                    await start_message.edit(embed=self.em(json['mode'], players_text))

        await ctx.em(
            title="**Clash finished**",
            description="\n".join(
                ["Results:"] + [
                    # Example "1. Takos (Code length: 123, Score 100%, Time 1:09)"
                    f"{p['rank']}. {p['codingamerNickname']} ("
                    + (f"Code length: {p['criterion']}, " if json["mode"] == "SHORTEST" else "")
                    + f"Score: {p['score']}%, Time: {p['duration'] // 60_000}:{p['duration'] // 1000 % 60:02})"
                    for p in sorted(json["players"], key=lambda p: p["rank"])
                ]
            )
        )

