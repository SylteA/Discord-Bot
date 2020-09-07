from discord.ext import commands
import discord

import aiohttp
import asyncio
import re
import secrets

from .utils.DataBase.coc_user import CocUser


coc_role = 729342805855567934
coc_channel = 729352136588263456
coc_message = 729355074085584918
REGEX = re.compile(r"https://www.codingame.com/clashofcode/clash/([0-9a-f]{39})")
COC_URL = "https://www.codingame.com/services/ClashOfCode/findClashByHandle"
USER_URL = "https://www.codingame.com/services/CodinGamer/findCodingamePointsStatsByHandle"


def setup(bot: commands.Bot):
    bot.add_cog(ClashOfCode(bot=bot))


class ClashOfCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tokens = {}

    @property
    def role(self):
        return self.bot.guild.get_role(coc_role)

    @staticmethod
    def clean(name: str):
        return name.replace("_", "\\_").replace("*", "\\*").replace(
            "`", "`\u200b").replace("@", "\\@")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
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

    @commands.group(name="clash-of-code", aliases=("coc", "invite"), invoke_without_command=True)
    @commands.has_any_role(
        511334601977888798,  # Tim
        580911082290282506,  # Admin
        511332506780434438,  # Mod
        541272748161499147,  # Helper
        coc_role
    )
    @commands.check(lambda ctx: ctx.channel.id == 729352136588263456)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def coc(self, ctx: commands.Context, *, url: str):
        """Mentions all the users with the `Clash Of Code` role that are currently online."""
        await ctx.message.delete()

        link = REGEX.fullmatch(url)
        if not link:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send('Could not find any valid "clashofcode" urls.')

        id = link[1]

        async with aiohttp.ClientSession() as session:
            async with session.post(COC_URL, json=[id]) as resp:
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

        for member in self.role.members:
            if member != ctx.author:
                if member.status != discord.Status.offline:
                    pager.add_line(member.mention + ", ")

        for page in pager.pages:
            await ctx.send(page)

        async with aiohttp.ClientSession() as session:
            while not json["started"]:
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(COC_URL, json=[id]) as resp:
                    json = await resp.json()

        players = len(json["players"])
        players_text = ', '.join([p['codingamerNickname'] for p in sorted(json['players'], key=lambda p: p['position'])])
        start_message = await ctx.em(
            title="**Clash started**",
            description=f"Mode: {json['mode']}\nPlayers: {self.clean(players_text)}"
        )

        async with aiohttp.ClientSession() as session:
            while not json["finished"] and all(
                all(
                    key in p.keys() for key in ["score", "duration"] + (["criterion"] if json["mode"] == "SHORTEST" else [])
                ) for p in json["players"]
            ):
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(COC_URL, json=[id]) as resp:
                    json = await resp.json()

                if len(json["players"]) != players:
                    players_text = ", ".join([p["codingamerNickname"] for p in sorted(json["players"], key=lambda p: p["position"])])
                    await start_message.edit(
                        embed=discord.Embed(
                            title="**Clash started**",
                            description=f"Mode: {json['mode']}\nPlayers: {self.clean(players_text)}")
                    )
                    players = len(json["players"])

        await ctx.em(
            title="**Clash finished**",
            description="\n".join(
                ["Results:"] + [
                    # Example "1. Takos (Code length: 123, Score 100%, Time 1:09)"
                    f"{p['rank']}. {self.clean(p['codingamerNickname'])} ("
                    + (f"Code length: {p['criterion']}, " if json["mode"] == "SHORTEST" else "")
                    + f"Score: {p['score']}%, Time: {p['duration'] // 60_000}:{p['duration'] // 1000 % 60:02})"
                    for p in sorted(json["players"], key=lambda p: p["rank"])
                ]
            )
        )

    @coc.command()
    async def bind(self, ctx: commands.Context, coc_id: str):
        """Binds a discord user to a CodinGame user."""

        coc_user: CocUser = await self.bot.db.get_coc_user(coc_id=coc_id)
        if coc_user is not None:
            return await ctx.send(f"You are already binded with CodinGamer '{coc_user.coc_id}'.")

        async with aiohttp.ClientSession() as session:
            async with session.post(USER_URL, json=[coc_id]) as resp:
                json = await resp.json()

            if json is None:
                return await ctx.send(
                    "Invalid CodinGamer id.\n"
                    "Do `t.tag codingamer id` to find your CodinGamer id."
                )

            codingamer = json["codingamer"]

            if codingamer["publicHandle"] in self.tokens.keys():
                if self.tokens[codingamer["publicHandle"]] in (
                    codingamer.get("tagline", ""),
                    codingamer.get("biography", "")
                ):
                    del self.tokens[codingamer["publicHandle"]]
                    coc_user = CocUser(self.bot, discord_id=ctx.author.id, coc_id=codingamer["publicHandle"])
                    await coc_user.post()
                    return await ctx.send(f"Succesfully binded with CodinGamer '{coc_user.coc_id}'.")
                else:
                    return await ctx.send(
                        f"Couldn't find the verification token on the profile of CodinGamer '{coc_user.coc_id}'.\n"
                        "Do `t.tag codingamer biography` to find out how to add the verification token."
                    )

            else:
                self.tokens[codingamer["publicHandle"]] = secrets.token_hex(16)
                try:
                    await ctx.author.send(
                        "Add this token to your CodinGamer profile: "
                        f"{self.tokens[codingamer['publicHandle']]}\n"
                        "Do `t.tag codingamer biography` to find out how to add the verification token."
                    )
                except discord.HTTPException:
                    await ctx.send("Please open your DMs so you can get your verification token in DMs. Otherwise you can't bind your CodinGame account.")
