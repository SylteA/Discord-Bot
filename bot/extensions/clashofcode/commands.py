import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.clashofcode.utils import coc_helper
from bot.extensions.clashofcode.views import CreateCocView


class ClashOfCode(commands.GroupCog, group_name="coc"):
    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        self._create_coc_view = CreateCocView(timeout=None)
        self.bot.add_view(self._create_coc_view)

    @app_commands.command()
    @app_commands.default_permissions()
    async def new(self, interaction: core.InteractionType):
        """Create a new coc for the session"""

        await interaction.response.send_message(
            "Select the programming languages and modes you want to use",
            ephemeral=True,
            view=self._create_coc_view,
        )

    @app_commands.command()
    @app_commands.default_permissions()
    async def end(self, interaction: core.InteractionType):
        """Ends the current coc session"""

        if not coc_helper.session:
            return await interaction.response.send_message("There is no active clash of code session", ephemeral=True)

        coc_helper.last_clash = 0
        coc_helper.session = False

        return await interaction.response.send_message(
            f"Clash session has been closed by {interaction.user.mention}. See you later",
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    async def interaction_check(self, interaction: core.InteractionType):
        if interaction.channel_id != settings.coc.channel_id:
            await interaction.response.send_message(
                "You need to be in the Clash Of Code channel to use this command", ephemeral=True
            )
            return False


async def setup(bot: core.DiscordBot):
    await bot.add_cog(ClashOfCode(bot=bot))
