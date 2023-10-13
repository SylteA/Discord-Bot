import discord
from discord.ext import commands

from bot import core
from bot.models import LevellingRole, PersistentRole


class LevelEvents(commands.Cog):
    """Events for Levelling in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_level_up(self, new_level, member: discord.Member):
        """Add roles when user levels up"""
        data = await LevellingRole.list_by_guild(guild_id=member.guild.id)
        for i in range(len(data)):
            # Adding roles when user levels up
            if new_level >= data[i].level and member.guild.get_role(data[i].role_id) not in member.roles:
                await member.add_roles(member.guild.get_role(data[i].role_id))
                await PersistentRole.insert_by_guild(
                    guild_id=member.guild.id, user_id=member.id, role_id=data[i].role_id
                )
            # Removing roles when users level down using remove_xp command
            elif new_level <= data[i].level and member.guild.get_role(data[i].role_id) in member.roles:
                await member.remove_roles(member.guild.get_role(data[i].role_id))
                await PersistentRole.delete_by_guild(guild_id=member.guild.id, user_id=member.id)
