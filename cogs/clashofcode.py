from discord.ext import commands
import discord

import aiohttp
import asyncio
import re


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

    @commands.command(name="clash-of-code", aliases=("coc", "invite"))
    @commands.has_any_role(
        511334601977888798,  # Tim
        580911082290282506,  # Admin
        511332506780434438,  # Mod
        541272748161499147,  # Helper
        coc_role
    )
    @commands.check(lambda ctx: ctx.channel.id == 729352136588263456)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def coc_invite(self, ctx: commands.Context, *, url: str):
        """Mentions all the users with the `Clash Of Code` role that are currently online."""
        await ctx.message.delete()

        link = REGEX.fullmatch(url)
        if not link:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send('Could not find any valid "clashofcode" urls.')

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

        for member in self.role.members:
            if member != ctx.author:
                if member.status != discord.Status.offline:
                    pager.add_line(member.mention + ", ")

        if not len(pager.pages):
            await ctx.send(f"{ctx.author.mention}, Nobody is online to play with <:pepesad:733816214010331197>")

        for page in pager.pages:
            await ctx.send(page)

        async with aiohttp.ClientSession() as session:
            while not json["started"]:
                await asyncio.sleep(10)  # wait 10s to avoid flooding the API
                async with session.post(API_URL, json=[id]) as resp:
                    json = await resp.json()

        players = len(json["players"])
        players_text = ', '.join([p['codingamerNickname'] for p in sorted(json['players'], key=lambda p: p['position'])])
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
