from discord.ext import commands
import discord

class Emoji(commands.Cog, name="emoji"):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        return True
    
    @commands.command()
    async def emoji(self, ctx, *, name):
        """Emoji"""
        emoji = discord.utils.get(ctx.message.guild.emojis, name = name)
        await ctx.send(emoji)
      
      
      

def setup(bot):
    bot.add_cog(Emoji(bot=bot))
