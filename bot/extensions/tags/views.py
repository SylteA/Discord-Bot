from datetime import datetime

import discord
from discord import ui

from bot import core
from bot.models import Tag


class Confirm(ui.View):
    # None until we get a result.
    result: bool | None = None

    async def wait(self) -> bool | None:
        """Waits and returns the result."""
        await super().wait()
        return self.result

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: core.InteractionType, _: ui.Button):
        await interaction.message.delete()
        self.stop()
        self.result = True

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: core.InteractionType, _: ui.Button):
        await interaction.message.delete()
        self.stop()
        self.result = False


class LogTagCreationView(ui.View):
    DELETE_CUSTOM_ID = "extensions:tags:delete"
    FEATURE_CUSTOM_ID = "extensions:tags:feature"

    def __init__(self, timeout: float = None):
        super().__init__(timeout=timeout)

    @staticmethod
    async def wait_for_confirmation(interaction: core.InteractionType, tag: Tag, reason: str):
        """If the tag name or content has changed, wait for confirmation that they really want to delete."""
        view = Confirm()

        prompt = reason + "\nAre you sure you want to delete the tag?"
        await interaction.response.send_message(prompt, view=view, ephemeral=True)

        if await view.wait():
            await tag.delete()

    @ui.button(label="DELETE", style=discord.ButtonStyle.danger, custom_id=DELETE_CUSTOM_ID)
    async def delete_tag(self, interaction: core.InteractionType, _: ui.Button) -> None:
        embed = interaction.message.embeds[-1]

        tag_id = int(discord.utils.get(embed.fields, name="id").value)
        name = discord.utils.get(embed.fields, name="name").value

        tag = await Tag.fetch_by_id(guild_id=interaction.guild.id, tag_id=tag_id)

        if tag is None:
            return await interaction.response.edit_message(view=None)

        if tag.content != embed.description:
            return await self.wait_for_confirmation(interaction, tag=tag, reason="Tag content has changed")

        if tag.name != name:
            return await self.wait_for_confirmation(interaction, tag=tag, reason="Tag name has changed")

        await tag.delete()

        embed.set_footer(text=f"Deleted by: {interaction.user.name}")
        embed.colour = discord.Color.brand_red()
        embed.timestamp = datetime.utcnow()

        return await interaction.response.edit_message(embed=embed, view=None)
