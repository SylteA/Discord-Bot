import discord
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.tags.views import LogTagCreationView
from bot.models import Tag


class TagEvents(commands.Cog):
    """Events for the tags extension."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        self._log_tag_creation_view = LogTagCreationView()
        self.bot.add_view(self._log_tag_creation_view)

    @property
    def tag_logs_channel(self) -> discord.TextChannel | None:
        return self.bot.guild.get_channel(settings.tags.log_channel_id)

    @commands.Cog.listener()
    async def on_tag_create(self, author: discord.User, tag: Tag) -> discord.Message:
        """Logs the creation of new tags."""
        embed = discord.Embed(
            title=f"Tag created: {tag.name}",
            color=discord.Color.brand_green(),
            description=tag.content,
        )
        embed.set_author(name=author.name.title(), icon_url=author.display_avatar.url)
        embed.add_field(name="id", value=str(tag.id))
        embed.add_field(name="name", value=tag.name)
        embed.add_field(name="author_id", value=str(tag.author_id))

        return await self.tag_logs_channel.send(embed=embed, view=self._log_tag_creation_view)

    @commands.Cog.listener()
    async def on_tag_edit(self, author: discord.User, before: Tag, after: Tag) -> discord.Message:
        """Logs updated tags."""
        embed_before = discord.Embed(
            title=f"Tag updated: {before.name}",
            color=discord.Color.brand_green(),
            description=before.content,
        )
        embed_before.set_author(name=author.name.title(), icon_url=author.display_avatar.url)
        embed_before.add_field(name="id", value=str(before.id))
        embed_before.add_field(name="name", value=before.name)
        embed_before.add_field(name="author id", value=str(before.author_id))

        embed_after = discord.Embed(
            title=f"Tag updated: {after.name}",
            color=discord.Color.brand_green(),
            description=after.content,
        )
        embed_after.set_author(name=author.name.title(), icon_url=author.display_avatar.url)
        embed_after.add_field(name="id", value=str(after.id))
        embed_after.add_field(name="name", value=after.name)
        embed_after.add_field(name="author id", value=str(after.author_id))

        return await self.tag_logs_channel.send(embeds=[embed_before, embed_after], view=self._log_tag_creation_view)

    @commands.Cog.listener()
    async def on_tag_delete(self, user: discord.User, tag: Tag) -> discord.Message:
        """Logs deleted tags."""
        embed = discord.Embed(
            title=f"Tag deleted: {tag.name}",
            color=discord.Color.red(),
            description=tag.content,
        )
        embed.set_author(name=user.name.title(), icon_url=user.display_avatar.url)
        embed.add_field(name="id", value=str(tag.id))
        embed.add_field(name="author_id", value=str(tag.author_id))

        return await self.tag_logs_channel.send(embed=embed)
