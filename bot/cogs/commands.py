import discord
from discord.ext import commands
from discord.utils import get

from utils.checks import is_staff


def predicate(ctx):
    return is_staff(ctx.author)


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._docs_cache = None

    @commands.command(name="suggest")
    async def suggestion(self, ctx, *, suggestion: str):
        """Make a poll/suggestion"""
        await ctx.message.delete()
        em = discord.Embed(description=suggestion)
        em.set_author(
            name=f"Suggestion by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        msg = await ctx.send(embed=em)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command(name="result", aliases=["show"])
    async def result(self, ctx, msg_link: str):
        """Get result of poll"""
        try:
            channel_id = int(msg_link.split("/")[-2])
            msg_id = int(msg_link.split("/")[-1])
            channel = ctx.guild.get_channel(channel_id)
            message = await channel.fetch_message(msg_id)
            reaction_upvote = get(message.reactions, emoji="👍")
            reaction_downvote = get(message.reactions, emoji="👎")
            if message.author != ctx.bot.user:
                if not message.embeds[0].author.name.startswith("Poll"):
                    return await ctx.send("That message is not a poll!")
            else:
                poll_embed = message.embeds[0]
                embed = discord.Embed(description=f"Suggestion: {poll_embed.description}")
                embed.set_author(name=poll_embed.author.name, icon_url=poll_embed.author.icon_url)
                embed.add_field(name="Upvotes:", value=f"{reaction_upvote.count} 👍")
                embed.add_field(name="Downvotes:", value=f"{reaction_downvote.count} 👎")
                await ctx.send(embed=embed)
        except Exception:
            return await ctx.send("That message is not a poll!")


async def setup(bot):
    await bot.add_cog(Commands(bot))
