from discord.ext import commands
import discord

import re

coc_role = 729342805855567934
coc_channel = 729352136588263456
coc_message = 729355074085584918
REGEX = re.compile(r"(https://www.codingame.com/clashofcode/clash/[^\s]+)")


def setup(bot: commands.Bot):
    bot.add_cog(ClashOfCode(bot=bot))


class ClashOfCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.role = self.bot.guild.get_role(coc_role)

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

        links = REGEX.findall(url)
        if not links:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f'Could not find any valid "clashofcode" urls.')

        if len(links) > 1:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f'Please only provide one "clashofcode" url.')

        pager = commands.Paginator(prefix=f'Hey, {ctx.author.mention} is hosting a "clashofcode" game!'
                                          f'\nJoin (or coward) here: {links[0]}',
                                   suffix="")
        for member in self.role.members:
            if member.status != discord.Status.offline:
                pager.add_line(member.mention + ", ")

        for page in pager.pages:
            await ctx.send(page)
