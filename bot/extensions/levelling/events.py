from bisect import bisect

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

    @commands.Cog.listener()
    async def on_xp_updated(self, data, member: discord.Member, required_xp):
        """Function to check if user's level has changed and trigger the event to assign the roles"""
        # Calculating old and new level
        try:
            old_level = bisect(required_xp, data.old_total_xp) - 1
            new_level = bisect(required_xp, data.total_xp) - 1

            if old_level != new_level:
                self.bot.dispatch("level_up", new_level=new_level, member=member)
        except AttributeError:
            pass
