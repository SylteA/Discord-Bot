import asyncio

import asyncpg
import discord
from discord import app_commands, ui
from discord.ext import commands

from bot import core
from bot.models import Model, Tag
from utils import checks

loop = asyncio.get_event_loop()


async def fetch_similar_tags(interaction: core.InteractionType, value: str) -> list[app_commands.Choice[str]]:
    """Fetches similar tags to the current value in the users search."""
    query = """
        SELECT name
          FROM tags
         WHERE guild_id = $1
           AND name % $2
         LIMIT 12
    """

    records = await Model.fetch(query, interaction.guild.id, value.lower())
    return [app_commands.Choice(name=name, value=name) for name, in records]


async def fetch_similar_owned_tags(interaction: core.InteractionType, value: str) -> list[app_commands.Choice[str]]:
    """Fetches similar tags owned by the user searching."""
    query = """
        SELECT name
          FROM tags
         WHERE author_id = $1
           AND guild_id = $2
           AND name % $3
         LIMIT 12
    """

    records = await Model.fetch(query, interaction.user.id, interaction.guild.id, value.lower())
    return [app_commands.Choice(name=name, value=name) for name, in records]


async def staff_tag_autocomplete(interaction: core.InteractionType, value: str) -> list[app_commands.Choice[str]]:
    if checks.is_staff(interaction.user):
        return await fetch_similar_tags(interaction, value)

    return await fetch_similar_owned_tags(interaction, value)


class MakeTagModal(ui.Modal, title="Create a new tag"):
    name = ui.TextInput(label="Name", required=True, max_length=64, min_length=1)
    content = ui.TextInput(label="Content", required=True, max_length=2000, min_length=1, style=discord.TextStyle.long)

    def __init__(self, cog: "Tags"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: core.InteractionType) -> None:
        await self.cog.create_tag(interaction=interaction, name=str(self.name), content=str(self.content))


class EditTagModal(ui.Modal, title="Edit tag"):
    name = ui.TextInput(label="Name", required=True, max_length=64, min_length=1)
    content = ui.TextInput(label="Content", required=True, max_length=2000, min_length=1, style=discord.TextStyle.long)

    def __init__(self, cog: "Tags", tag: Tag):
        super().__init__()
        self.cog = cog

        self.tag = tag

        self.name.default = tag.name
        self.content.default = tag.content

    async def on_submit(self, interaction: core.InteractionType) -> None:
        await self.cog.edit_tag(interaction=interaction, tag=self.tag, name=str(self.name), content=str(self.content))


class Tags(commands.Cog, group_name="tag"):
    """Commands to fetch content by tag names."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        app_commands.guild_only(self)

    tags = app_commands.Group(name="tags", description="Commands to manage tags.")
    tags.default_permissions = discord.Permissions(administrator=True)

    @app_commands.command()
    @app_commands.autocomplete(name=fetch_similar_tags)
    @app_commands.describe(name="The name of the tag to get.")
    async def tag(self, interaction: core.InteractionType, name: str):
        """Sends the content associated with the tag specified."""
        tag = await Tag.fetch_by_name(guild_id=interaction.guild.id, name=name)

        if tag is None:
            response = "There is no tag with that name"

            choices = await fetch_similar_tags(interaction=interaction, value=name)

            if choices:
                response += "\n\nDid you mean one of these?"

            for choice in choices[:6]:
                response += f"\n - {choice.name}"

            return await interaction.response.send_message(response, ephemeral=True)

        await interaction.response.send_message(tag.content)

        query = "UPDATE tags SET uses = uses + 1 WHERE guild_id = $1 AND name = $2"
        await Tag.execute(query, interaction.guild.id, tag.name)

    @staticmethod
    async def validate_tag(interaction: core.InteractionType, name: str, content: str) -> None | bool:
        if len(content) > 2000:
            return await interaction.response.send_message(
                "Tag content must be 2000 or less characters.", ephemeral=True
            )

        name = name.lower().strip()

        if not name:
            return await interaction.response.send_message("Missing tag name.", ephemeral=True)

        if len(name) > 64:
            return await interaction.response.send_message("Tag names must be 64 or less characters.", ephemeral=True)

        return True

    async def edit_tag(self, interaction: core.InteractionType, tag: Tag, name: str, content: str) -> Tag | None:
        if not await self.validate_tag(interaction=interaction, name=name, content=content):
            return

        try:
            after = await tag.edit(name=name, content=content)
        except asyncpg.UniqueViolationError:
            return await interaction.response.send_message("A tag with that name already exists!", ephemeral=True)

        self.bot.dispatch("tag_edit", author=interaction.user, before=tag, after=after)

        await interaction.response.send_message(content="Your tag has been edited!", ephemeral=True)
        return after

    async def create_tag(self, interaction: core.InteractionType, name: str, content: str) -> Tag | None:
        if not await self.validate_tag(interaction=interaction, name=name, content=content):
            return

        try:
            tag = await Tag.create(
                guild_id=interaction.guild.id,
                author_id=interaction.user.id,
                name=name,
                content=content,
            )
        except asyncpg.UniqueViolationError:
            return await interaction.response.send_message("A tag with that name already exists!", ephemeral=True)

        self.bot.dispatch("tag_create", author=interaction.user, tag=tag)

        await interaction.response.send_message(content="Your tag has been created!", ephemeral=True)
        return tag

    @tags.command()
    @app_commands.describe(name="Tag name", content="Tag content")
    async def create(self, interaction: core.InteractionType, name: str, *, content: str):
        """Creates a tag owned by you."""
        return await self.create_tag(interaction=interaction, name=name, content=content)

    @tags.command()
    async def make(self, interaction: core.InteractionType):
        """Starts an interactive session to create your tag."""
        await interaction.response.send_modal(MakeTagModal(cog=self))

    @tags.command()
    @app_commands.autocomplete(name=fetch_similar_tags)
    @app_commands.describe(name="The name of the tag to show.")
    async def info(self, interaction: core.InteractionType, name: str):
        """Shows information about the tag with the given name."""
        tag = await Tag.fetch_by_name(guild_id=interaction.guild.id, name=name)

        if tag is None:
            return await interaction.response.send_message("There is no tag with that name", ephemeral=True)

        author = self.bot.get_user(tag.author_id)
        author = str(author) if isinstance(author, discord.User) else f"(ID: {tag.author_id})"
        text = f"Tag: {name}\n\n```prolog\nCreator: {author}\n   Uses: {tag.uses}\n```"
        await interaction.response.send_message(content=text, ephemeral=True)

    @tags.command()
    @app_commands.autocomplete(name=staff_tag_autocomplete)
    @app_commands.describe(name="The name of the tag to edit.")
    async def edit(self, interaction: core.InteractionType, name: str):
        """Edit the tag with this name"""
        tag = await Tag.fetch_by_name(guild_id=interaction.guild.id, name=name)

        if tag is None:
            return await interaction.response.send_message("There is no tag with that name", ephemeral=True)

        if not checks.is_staff(interaction.user):
            if tag.author_id != interaction.user.id:
                return await interaction.response.send_message("You do not own this tag", ephemeral=True)

        await interaction.response.send_modal(EditTagModal(cog=self, tag=tag))

    @tags.command()
    @app_commands.autocomplete(name=staff_tag_autocomplete)
    @app_commands.describe(name="The name of the tag to delete.")
    async def delete(self, interaction: core.InteractionType, name: str):
        """Deletes the specified tag."""
        tag = await Tag.fetch_by_name(guild_id=interaction.guild.id, name=name)

        if tag is None:
            return await interaction.response.send_message("There is no tag with that name", ephemeral=True)

        if not checks.is_staff(interaction.user):
            if tag.author_id != interaction.user.id:
                return await interaction.response.send_message("You do not own this tag", ephemeral=True)

        await tag.delete()
        self.bot.dispatch("tag_delete", user=interaction.user, tag=tag)
        return await interaction.response.send_message(f'Tag "{tag.name}" has been deleted!', ephemeral=True)

    @tags.command()
    @app_commands.describe(user="The user to filter by.")
    async def list(self, interaction: core.InteractionType, user: discord.Member = None):
        """List the existing tags of the specified member."""
        user = user or interaction.user
        query = "SELECT name FROM tags WHERE guild_id = $1 AND author_id = $2 ORDER BY name"

        records = await Tag.fetch(query, interaction.guild.id, user.id, convert=False)

        pronoun = "you" if user == interaction.user else user.display_name

        if not records:
            return await interaction.response.send_message(f"No tags by {pronoun} found.", ephemeral=True)

        pager = commands.Paginator(prefix="", suffix="")
        pager.add_line(f"## {len(records)} tags by {pronoun} found on this server.")

        for (name,) in records:
            pager.add_line("- " + name)

        await interaction.response.send_message(pager.pages[0])

        for page in pager.pages[1:]:
            await interaction.followup.send(page)
