import discord
from discord.ext import commands

class QandA(commands.Cog):
  @commands.Cog.listener()
  async def on_message(self, message):
    role = discord.Object(id=795257055093981194)
    if message.channel.id == 795256498958630952:
      if role not in message.author.roles:
        await message.author.add_roles(role)

def setup(bot):
  bot.add_cog(QandA())
