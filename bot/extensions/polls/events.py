import discord
from discord.ext import commands

from bot import core
from bot.extensions.polls.utils import emojis, poll_check


class PollEvents(commands.Cog):
    """Events for polls in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)

        try:
            message: discord.Message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if payload.user_id == self.bot.user.id:
            return

        if not poll_check(message, self.bot.user):
            return

        if str(payload.emoji) not in emojis:
            return

        for reaction in message.reactions:
            if str(reaction) not in emojis:
                return

            if str(reaction.emoji) != str(payload.emoji):
                user = self.bot.get_user(payload.user_id)
                await message.remove_reaction(reaction.emoji, user)
