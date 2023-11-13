from __future__ import annotations

import discord
from discord import app_commands, utils
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.models import CustomRole


class CustomRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.color_converter = commands.ColorConverter()

    @staticmethod
    def role_embed(heading: str, role: discord.Role):
        embed = discord.Embed(
            description=f"# {heading}",
            timestamp=role.created_at,
            color=role.color,
        )
        embed.add_field(name="Name", value=utils.escape_markdown(role.name))
        embed.add_field(name="Color", value=str(role.color))
        embed.set_footer(text="Created at")
        return embed

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(name="New name", color="New color")
    async def myrole(
        self, interaction: core.InteractionType, name: app_commands.Range[str, 2, 100] | None, color: str = None
    ):
        """Manage your custom role"""
        if color is not None:
            try:
                color = await self.color_converter.convert(None, color)  # noqa
            except commands.BadColourArgument as e:
                return await interaction.response.send_message(str(e), ephemeral=True)

        query = "SELECT * FROM custom_roles WHERE guild_id = $1 AND user_id = $2"
        before = await CustomRole.fetchrow(query, interaction.guild.id, interaction.user.id)

        if before is None:
            if name is None:
                return await interaction.response.send_message("You don't have a custom role yet!", ephemeral=True)

            # Create and assign the role to user
            role = await interaction.guild.create_role(name=name, colour=color or discord.Color.random())

            divider_role = interaction.guild.get_role(settings.custom_roles.divider_role_id)
            await role.edit(position=divider_role.position + 1)

            record = await CustomRole.ensure_exists(
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                role_id=role.id,
                name=role.name,
                color=role.color.value,
            )

            self.bot.dispatch("custom_role_create", custom_role=record)
            self.bot.dispatch(
                "persist_roles",
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                role_ids=[role.id],
            )

            return await interaction.response.send_message(
                embed=self.role_embed("**Custom Role has been assigned**", role),
                ephemeral=True,
            )

        role = interaction.guild.get_role(before.role_id)

        # Return role information if no parameter is passed
        if (name is None or name == before.name) and (color is None or color.value == before.color):
            return await interaction.response.send_message(
                embed=self.role_embed(
                    f"Custom Role for {interaction.user.mention}", interaction.guild.get_role(before.role_id)
                ),
                ephemeral=True,
            )

        await role.edit(
            name=name or before.name,
            colour=color or discord.Color(int(before.color)),
        )

        after = await CustomRole.ensure_exists(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            role_id=role.id,
            name=role.name,
            color=role.color.value,
        )

        self.bot.dispatch("custom_role_update", before, after)

        return await interaction.response.send_message(
            embed=self.role_embed("**Custom Role has been updated**", interaction.guild.get_role(before.role_id)),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomRoles(bot=bot))
