import discord
from aiohttp import ContentTypeError
from codingame.http import HTTPError
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.clashofcode.utils import coc_client, coc_helper
from bot.extensions.clashofcode.views import CreateCocView


@app_commands.default_permissions(administrator=True)
class ClashOfCode(commands.GroupCog, group_name="coc"):
    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        self._create_coc_view = CreateCocView(timeout=None)
        self.bot.add_view(self._create_coc_view)

    async def cog_load(self):
        await coc_client.login(remember_me_cookie=settings.coc.session_cookie)

    async def interaction_check(self, interaction: core.InteractionType):
        if interaction.channel_id != settings.coc.channel_id:
            await interaction.response.send_message(
                "You need to be in the Clash Of Code channel to use this command", ephemeral=True
            )
            return False
        return True

    @app_commands.command()
    async def new(self, interaction: core.InteractionType):
        """Create a new coc for the session"""

        await interaction.response.send_message(
            "Select the programming languages and modes you want to use",
            ephemeral=True,
            view=self._create_coc_view,
        )

    @app_commands.command()
    async def start(self, interaction: core.InteractionType):
        """Starts the current clash"""

        if not coc_helper.session:
            return await interaction.response.send_message("There is no active clash of code session", ephemeral=True)

        if coc_helper.clash.started:
            return await interaction.response.send_message("The clash has already started", ephemeral=True)

        try:
            await coc_client.request(
                "ClashOfCode", "startClashByHandle", [coc_client.codingamer.id, coc_helper.clash.public_handle]
            )
        except HTTPError:
            return await interaction.response.send_message(
                "An error occurred while starting the clash. Please try again later", ephemeral=True
            )
        except ContentTypeError:
            # Issue with the codingame library always assuming the response is JSON
            pass

        await interaction.response.send_message(
            "Clash started!",
            ephemeral=False,
        )

    @app_commands.command()
    async def end(self, interaction: core.InteractionType):
        """Ends the current coc session"""

        if not coc_helper.session:
            return await interaction.response.send_message("There is no active clash of code session", ephemeral=True)

        coc_helper.last_clash = 0
        coc_helper.session = False
        coc_helper.clash = None

        return await interaction.response.send_message(
            f"Clash session has been closed by {interaction.user.mention}. See you later",
            allowed_mentions=discord.AllowedMentions(users=True),
        )
