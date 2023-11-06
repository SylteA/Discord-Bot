import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.config import settings


class YoutubeCommands(commands.GroupCog, group_name="youtube"):
    """Commands for YouTube commands"""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @property
    def youtube_role(self) -> discord.Role | None:
        return self.bot.guild.get_role(settings.notification.role_id)

    @app_commands.command()
    async def subscribe(self, interaction: core.InteractionType):
        """Subscribe to receive notifications for new uploads"""

        if self.youtube_role in interaction.user.roles:
            return await interaction.response.send_message(
                "You are already subscribed to YouTube notifications", ephemeral=True
            )

        await interaction.user.add_roles(self.youtube_role, reason="Subscribed to YouTube notifications")
        await interaction.response.send_message(
            "Successfully subscribed you to receive notifications for new uploads", ephemeral=True
        )

    @app_commands.command()
    async def unsubscribe(self, interaction: core.InteractionType):
        """Unsubscribe from receiving notifications for new uploads"""

        if self.youtube_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "You are not subscribed to YouTube notifications", ephemeral=True
            )

        await interaction.user.remove_roles(self.youtube_role, reason="Unsubscribed from YouTube notifications")
        await interaction.response.send_message(
            "Successfully unsubscribed you from receiving notifications for new uploads", ephemeral=True
        )


async def setup(bot: core.DiscordBot):
    await bot.add_cog(YoutubeCommands(bot=bot))
