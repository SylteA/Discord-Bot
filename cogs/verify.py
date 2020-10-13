import discord
from discord.ext import commands
import asyncio

import time

from .utils.checks import is_mod

import random

verification_message = 764935446345285683
verification_channel = 764919169548025926

class UserVerification:
  def __init__(self, id, time, member):
    self.verification = str(id) 
    self.time = time
    self.tries = 0
    self.member = member
    self.notified = False
  
  async def verify(self, verification, bot):
    self.tries += 1
    if self.tries > 5 and not self.notified:
      log_channel = bot.guild.get_channel(536617175369121802)
      await log_channel.send(f"{self.member.mention} has tried verifying the same code more than 5 times")
      self.notified = True  
    if str(verification) == self.verification:
      return True
    return False

class Verify(commands.Cog):
  def __init__(self, bot):
    self.__bot = bot
    self.users = {}

  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
    if payload.message_id != verification_message:
      return

    if payload.member.bot:
      return
    
    if str(payload.emoji) != '🖐️':
      return
    
    message = await self.__bot.get_channel(verification_channel).fetch_message(verification_message)
    await message.remove_reaction(payload.emoji, payload.member)
    
    verification = random.randint(100000, 999999)
    try:
      await payload.member.send("Verification Code (expires in 5 minutes):")
      await payload.member.send(f"**{verification}**")
      self.users[payload.user_id] = UserVerification(verification, int(time.time()), payload.member)
    except:
      await self.__bot.guild.get_channel(verification_channel).send(f"{payload.member.mention}, Please enable direct message to receive your verification code. If you have already enabled it and still facing issues, please contact a member of staff.", delete_after=10.0)

  @property
  def verified_role(self):
    return self.__bot.guild.get_role(612391389086351363)

  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.channel.id != verification_channel:
      return
    if message.author == self.__bot.user:
      return
    if is_mod(message.author):
      return
    await message.delete()
    if message.author.bot:
      return
    verify = message.content
    try:
      if self.users[message.author.id].time + 300 < int(time.time()):
        return await message.channel.send(f"{message.author.mention}, The verification code you have has timedout please get another one", delete_after=10)
      verified = await self.users[message.author.id].verify(verify, self.__bot)
      if verified:
        await message.channel.send(f"{message.author.mention}, You have been verified. Welcome to the server.", delete_after=10)
        await asyncio.sleep(2)
        await message.author.add_roles(self.verified_role)
      else:
        await message.channel.send(f"{message.author.mention}, Invalid verification code. Please try again", delete_after=10)
    except KeyError:
      await message.channel.send(f"{message.author.mention}, make sure that you recived a verification code before trying to verify", delete_after=10)


def setup(bot):
  bot.add_cog(Verify(bot))
