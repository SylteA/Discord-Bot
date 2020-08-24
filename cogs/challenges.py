from discord.ext import commands
import discord
from ..discordIds import *


def setup(bot):
    bot.add_cog(ChallengeHandler(bot))


class ChallengeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Participant role.
        if payload.emoji != discord.PartialEmoji(name="🖐️"):
            return

        if payload.channel_id == weeklyChallenge:
            submitted = self.bot.guild.get_role(weeklySubmittedRole)
            if submitted in payload.member.roles:
                return

            participant = self.bot.guild.get_role(weeklyParticipantRole)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

        elif payload.channel_id == monthlyChallenge:
            submitted = self.bot.guild.get_role(monthlySubmittedRole)
            if submitted in payload.member.roles:
                return

            participant = self.bot.guild.get_role(monthlyParticipantRole)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

    @commands.Cog.listener()
    async def on_message(self, message):  # Submitted role.
        if message.author.bot:
            return

        if message.channel.id == weeklySubmit:  # weekly

            submitted = self.bot.guild.get_role(weeklySubmittedRole)
            participant = self.bot.guild.get_role(weeklyParticipantRole)
            submission_channel = self.bot.guild.get_channel(weeklyHiddenSolution)

            if submitted not in message.author.roles:
                await message.delete()
                if message.content.count("```") != 2:
                    message.channel.send("Make sure to submit your code in a code block\n```python\nyour code here\n```")
                    return
                await message.author.add_roles(submitted)
                await message.author.remove_roles(participant)
                embed = discord.Embed(description=message.content,
                                      color=message.guild.me.top_role.color)
                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
                embed.set_footer(text=f'#ID: {message.author.id}')
                await submission_channel.send(embed=embed)

        elif message.channel.id == monthlySubmit:  # monthly 

            submitted = self.bot.guild.get_role(monthlySubmittedRole)
            participant = self.bot.guild.get_role(monthlyParticipantRole)
            submission_channel = self.bot.guild.get_channel(monthlyHiddenSolution)

            if submitted not in message.author.roles:
                await message.author.add_roles(submitted)
                await message.author.remove_roles(participant)
                await message.delete()
                embed = discord.Embed(description=message.content,
                                      color=message.guild.me.top_role.color)
                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
                embed.set_footer(text=f'#ID: {message.author.id}')
                await submission_channel.send(embed=embed)

        elif message.channel.id in [weeklyChallenge, monthlyChallenge]:  # Automatic reaction
            await message.add_reaction("🖐️")
