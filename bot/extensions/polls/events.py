import discord
from discord.ext import commands

from bot import core


class PollsEvents(commands.Cog):
    """Events for polls in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "9️⃣", "🔟"]

    def poll_check(self, message: discord.Message):
        try:
            embed = message.embeds[0]
        except Exception:
            return False
        if str(embed.footer.text).count("Poll by") == 1:
            return message.author == self.bot.user
        return False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        channel: discord.TextChannel = self.bot.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)

        if payload.user_id == self.bot.user.id:
            return

        if not self.poll_check(message):
            return

        if str(payload.emoji) not in self.emojis:
            return

        for reaction in message.reactions:
            if str(reaction) not in self.emojis:
                return

            if str(reaction.emoji) != str(payload.emoji):
                user = self.bot.get_user(payload.user_id)
                await message.remove_reaction(reaction.emoji, user)
