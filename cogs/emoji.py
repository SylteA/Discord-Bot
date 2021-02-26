from discord.ext import commands
import discord

class Emoji(commands.Cog, name="emoji"):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        return True
      
      
      

def setup(bot):
    bot.add_cog(Emoji(bot=bot))
