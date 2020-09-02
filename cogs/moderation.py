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
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def report(self, ctx, user: discord.Member, *, reason: str):
        """Report a user to staff for a reason."""
        if user.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't warn a bot <:mhm:687726663676592145>")

        embed = discord.Embed(title=f"Report")
        embed.add_field(name="Reported User", value=user.mention)
        embed.add_field(name="Reporter", value=ctx.author.mention)
        embed.add_field(name="Reported On", value=f"{datetime.datetime.now().strftime('%a, %b %d, %Y %I:%M %p')}")
        embed.add_field(name="Reason", value=reason, inline=False)

        await ctx.send(embed=embed)
        await self.report_channel.send(embed=embed)
