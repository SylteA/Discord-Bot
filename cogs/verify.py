import discord
from discord.ext import commands
import asyncio

import time

class Verify(commands.Cog):
  def __init__(self, bot):
    self.__bot = bot
  
  @commands.Cog.listener()
  async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not after.pending and before.pending:
            return await after.add_roles(discord.Object(id=612391389086351363))
        if (roles := (set(after.roles) - set(before.roles))):  # If there is a new role
            if 605779930529136658 in [r.id for r in roles]:  # If lvl 1 is one of the roles
                return await after.add_roles(discord.Object(id=612391389086351363))

def setup(bot):
  bot.add_cog(Verify(bot))
