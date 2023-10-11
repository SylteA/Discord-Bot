import logging

import discord
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.models import LevellingRole, PersistentRole

log = logging.getLogger(__name__)


class ChallengeEvents(commands.Cog):
    """Events for weekly challenges in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    challenge_reaction = discord.PartialEmoji(name="🖐️")

    @property
    def submitted_role(self) -> discord.Role | None:
        return self.bot.guild.get_role(settings.challenges.submitted_role_id)

    @property
    def participant_role(self) -> discord.Role | None:
        return self.bot.guild.get_role(settings.challenges.participant_role_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Automatically react to new challenges."""

        if message.channel.id != settings.challenges.channel_id:
            return

        await message.add_reaction(self.challenge_reaction)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id != settings.challenges.channel_id:
            return

        if payload.emoji != self.challenge_reaction:
            return

        if self.submitted_role in payload.member.roles:
            return

        await self.bot.http.add_role(
            guild_id=self.bot.guild.id, user_id=payload.user_id, role_id=self.participant_role.id
        )

    @commands.Cog.listener()
    async def on_level_up(self, new_level, member: discord.Member):
        """Add roles when user levels up"""
        data = await LevellingRole.get(guild_id=member.guild.id)
        for i in range(len(data)):
            # Adding roles when user levels up
            if new_level >= data[i].level and member.guild.get_role(data[i].role_id) not in member.roles:
                await member.add_roles(member.guild.get_role(data[i].role_id))
                await PersistentRole.insert(guild_id=member.guild.id, user_id=member.id, role_id=data[i].role_id)
            # Removing roles when users level down using remove_xp command
            elif new_level <= data[i].level and member.guild.get_role(data[i].role_id) in member.roles:
                await member.remove_roles(member.guild.get_role(data[i].role_id))
                await PersistentRole.remove(guild_id=member.guild.id, user_id=member.id)
