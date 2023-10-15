import datetime
import random

import asyncpg.exceptions
import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.models import IgnoredChannel, LevellingRole, Levels
from bot.models.custom_roles import CustomRoles


class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignored_channel = {}
        self.required_xp = [0]

    async def cog_load(self):
        for guild in self.bot.guilds:
            data = await IgnoredChannel.list_by_guild(guild_id=guild.id)
            for i in data:
                if guild.id not in self.ignored_channel:
                    self.ignored_channel[guild.id] = [i.channel_id]
                else:
                    self.ignored_channel[guild.id].append(i.channel_id)

        # Calculating required_XP for next level and storing in a list, list-index corresponds to the level
        for lvl in range(101):
            xp = 5 * (lvl**2) + (50 * lvl) + 100
            self.required_xp.append(xp + self.required_xp[-1])

    @commands.Cog.listener()
    async def on_message(self, message):
        # Return if message was sent by Bot or sent in DMs
        if message.author.bot or message.guild is None:
            return

        # Check if message is sent in ignored channel
        try:
            if message.channel.id in self.ignored_channel[message.guild.id]:
                return
        except KeyError:
            pass

        # Generate random XP to be added
        xp = random.randint(5, 25)
        # Add the XP and update the DB
        data = await Levels.insert_by_guild(guild_id=message.guild.id, user_id=message.author.id, total_xp=xp)
        self.bot.dispatch("xp_updated", data=data, member=message.author, required_xp=self.required_xp)

    @app_commands.command()
    async def rank(self, interaction: core.InteractionType, member: discord.Member = None):
        """Check the rank of another member or yourself"""
        if member is None:
            member = interaction.user
        query = """WITH ordered_users AS (
                 SELECT id,user_id,guild_id,total_xp,
            ROW_NUMBER() OVER (ORDER BY levelling_users.total_xp DESC) AS rank
                    FROM levelling_users
                    WHERE guild_id = $2)
                   SELECT id,rank,total_xp,user_id,guild_id
                     FROM ordered_users WHERE ordered_users.user_id = $1;"""
        data = await Levels.fetchrow(query, member.id, member.guild.id)
        if data is None:
            return await interaction.response.send_message("User Not ranked yet!", ephemeral=True)
        for level, j in enumerate(self.required_xp):
            if data.total_xp <= j:
                embed = discord.Embed(
                    title=f"Rank: {data.rank}\nLevel: {level - 1}\nTotal XP:{data.total_xp}",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.blurple(),
                )
                embed.set_thumbnail(url=member.avatar)
                return await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def ignore_channel(self, interaction: core.InteractionType, channel: discord.TextChannel):
        """Add the channel to the ignored channel list to not gain XP"""
        await IgnoredChannel.insert_by_guild(channel.guild.id, channel.id)
        await interaction.response.send_message(f"{channel} has been ignored from gaining XP.")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def unignore_channel(self, interaction: core.InteractionType, channel: discord.TextChannel):
        """Remove channel from ignored channel list"""
        await IgnoredChannel.delete_by_guild(channel.guild.id, channel.id)
        await interaction.response.send_message(f"{channel} has been removed from ignored channel list")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def give_xp(self, interaction: core.InteractionType, xp: int, member: discord.Member):
        """Give XP to specific user"""
        if xp <= 0:
            return await interaction.response.send_message("XP can not be less than 0")
        try:
            data = await Levels.give_xp(member.guild.id, member.id, xp)
            self.bot.dispatch("xp_updated", data=data, member=member, required_xp=self.required_xp)
            await interaction.response.send_message(f"{xp} XP has been added to user {member}")
        except asyncpg.exceptions.DataError:
            return await interaction.response.send_message("Invalid XP provided")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_xp(self, interaction: core.InteractionType, xp: int, member: discord.Member):
        """Remove XP from user"""
        if xp <= 0:
            return await interaction.response.send_message("XP can not be less than 0")
        try:
            data = await Levels.remove_xp(member.guild.id, member.id, xp)
            self.bot.dispatch("xp_updated", data=data, member=member, required_xp=self.required_xp)
            await interaction.response.send_message(f"{xp} XP has been removed from user {member}")
        except asyncpg.exceptions.DataError:
            return await interaction.response.send_message("Invalid XP provided")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def levelling_rewards_add(self, interaction: core.InteractionType, role: discord.Role, level: int):
        await CustomRoles.insert_by_guild(role.id, role.guild.id, role.name, str(role.colour))
        await LevellingRole.insert_by_guild(role.guild.id, role.id, level)
        return await interaction.response.send_message("Levelling reward role added")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def levelling_rewards_remove(self, interaction: core.InteractionType, role: discord.Role):
        await LevellingRole.delete_by_guild(role.guild.id, role.id)
        return await interaction.response.send_message("Levelling reward role removed")


async def setup(bot: commands.Bot):
    await bot.add_cog(Levelling(bot=bot))
