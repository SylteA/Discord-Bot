import discord
from discord.ext import commands

import datetime


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot=bot))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
