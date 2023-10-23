import asyncio

import discord
from discord import app_commands, ui
from discord.ext import commands

from bot import core
from utils.transformers import MessageTransformer

THUMBS_UP = "👍"
THUMBS_DOWN = "👎"


class SuggestionModal(ui.Modal, title="Suggestion"):
    suggestion = ui.TextInput(
        label="Suggestion",
        required=True,
        style=discord.TextStyle.paragraph,
        min_length=1,
        max_length=2000,
    )

    async def on_submit(self, interaction: core.InteractionType):
        embed = discord.Embed(description=str(self.suggestion), color=interaction.user.accent_color)
        embed.set_author(
            name=f"{Suggestions.SUGGESTION_AUTHOR_PREFIX} {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.response.send_message(embed=embed)

        message = await interaction.original_response()
        await asyncio.gather(message.add_reaction(THUMBS_UP), message.add_reaction(THUMBS_DOWN))


@app_commands.guild_only()
class Suggestions(commands.GroupCog, group_name="suggestion"):
    """Commands for suggestions"""

    SUGGESTION_AUTHOR_PREFIX = "Suggestion by"

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @app_commands.command()
    async def create(self, interaction: core.InteractionType):
        """Opens a modal to create a new suggestion"""
        await interaction.response.send_modal(SuggestionModal())

    @app_commands.command()
    async def result(
        self,
        interaction: core.InteractionType,
        message: app_commands.Transform[discord.Message, MessageTransformer],
    ):
        """View the results of a suggestion"""
        not_a_suggestion = "That message doesn't look like a suggestion..."

        if message.author != interaction.client.user:
            return await interaction.response.send_message(not_a_suggestion, ephemeral=True)

        if not message.embeds:
            return await interaction.response.send_message(not_a_suggestion, ephemeral=True)

        suggestion = message.embeds[0].description
        author = message.embeds[0].author

        if not author.name.startswith(self.SUGGESTION_AUTHOR_PREFIX):
            return await interaction.response.send_message(not_a_suggestion, ephemeral=True)

        upvotes = discord.utils.get(message.reactions, emoji=THUMBS_UP)
        downvotes = discord.utils.get(message.reactions, emoji=THUMBS_DOWN)

        embed = discord.Embed(description=f"Suggestion: {suggestion}")
        embed.set_author(name=author.name, icon_url=author.icon_url)
        embed.add_field(name="Upvotes", value=f"{upvotes.count} {THUMBS_UP}")
        embed.add_field(name="Downvotes", value=f"{downvotes.count} {THUMBS_DOWN}")
        return await interaction.response.send_message(embed=embed)
