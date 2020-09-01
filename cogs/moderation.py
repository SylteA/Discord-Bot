import discord
from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot=bot))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def report_channel(self):
        return self.bot.get_channel(749742688521158656)

    @commands.command("report")
    @commands.dm_only()
    async def report(self, ctx, user: discord.User, *, reason: str):
        """Report a user to staff for a reason."""
        await ctx.em(title=f"**Thank you for reporting {user} for:**", description=reason)
        em = discord.Embed(title=f"**Report {user} for:**", description=reason)
        em.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        await self.report_channel.send(embed=em)

