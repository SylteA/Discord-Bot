from discord.ext import commands
import discord
from ..discordIds import *

import re

REGEX = re.compile(r"(https://www.codingame.com/clashofcode/clash/[0-9a-f]{39})")

def setup(bot: commands.Bot):
    bot.add_cog(ClashOfCode(bot=bot))


class ClashOfCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def role(self):
        return self.bot.guild.get_role(cocRole)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != cocMessage:
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
        if payload.message_id != cocMessage:
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
        TIM,  # Tim
        adminRole,  # Admin
        modRole,  # Mod
        helperRole,  # Helper
        cocRole
    )
    @commands.check(lambda ctx: ctx.channel.id == cocChannel)
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
                                          f'\nJoin here: {links[0]}',
                                   suffix="")
        for member in self.role.members:
            if member.status != discord.Status.offline:
                if member != ctx.author:
                    pager.add_line(member.mention + ", ")

        for page in pager.pages:
            await ctx.send(page)
