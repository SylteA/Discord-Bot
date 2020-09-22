import discord
from discord.ext import commands

import datetime


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot=bot))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def report_channel(self):
        return self.bot.get_channel(749742688521158656)

    @commands.command("report")
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def report(self, ctx, member: discord.Member, *, reason: str):
        """Report a user to staff for a reason."""
        await ctx.message.delete()
        
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't report a bot <:mhm:687726663676592145>")
        
        if member.id == ctx.author.id : 
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't report your self <:mhm:687726663676592145>")

        thx_embed = discord.Embed(title="Report", timestamp=datetime.datetime.utcnow())
        thx_embed.description = f"Thank you for reporting `{str(member)}` for `{reason}`"
        thx_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        
        embed = discord.Embed(title=f"Report", timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Reported Member", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Reporter", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        try:
            await ctx.author.send(embed=thx_embed)
        except discord.Forbidden:
            await ctx.send(embed=thx_embed, delete_after=10)
            
        await self.report_channel.send(embed=embed)
        
