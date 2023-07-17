import logging

import discord
from discord.ext import commands

from bot import core
from bot.config import settings

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
