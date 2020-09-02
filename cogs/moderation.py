import discord
from discord.ext import commands
from datetime.datetime import now


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
    async def report(self, ctx, user: discord.User, *, reason: str):
        """Report a user to staff for a reason."""
        if user.bot:
            return await ctx.send("You cannot report a bot")
        await ctx.em(title=f"**Thank you for reporting {user} for:**", description=reason)
        em = discord.Embed(title=f"**Report**", color=discord.Colour.red())
        em.add_field(name="Reported User", value=user.display_name)
        em.add_field(name="Reporter", value=ctx.author.display_name)
        em.add_field(name="Channel", value=ctx.message.channel.mention)
        em.add_field(name="Reason", value=reason)
        em.set_footer(text=f"{ctx.author.display_name} | {str(now())}", icon_url=ctx.author.avatar_url)
        await self.report_channel.send(embed=em)

