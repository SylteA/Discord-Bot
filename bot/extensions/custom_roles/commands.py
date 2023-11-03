import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import escape_markdown, format_dt

from bot import core
from bot.models import CustomRole


class CustomRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def role_embed(self, heading: str, user: discord.Member, role: discord.Role):
        embed = discord.Embed(
            description=f"### {heading} {user.mention}\n\n**Name**\n{escape_markdown(role.name)}\n**Color**\n"
            f"{role.color}\n**Created**\n {format_dt(role.created_at)}",
            color=role.color,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_footer(text=user.name)
        embed.set_thumbnail(url=user.avatar)
        return embed

    @app_commands.command(description="Manage custom role")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(name="Updating Custom Role name", color="Updating custom role name")
    async def myrole(self, interaction: core.InteractionType, name: str = None, color: str = None):
        if color:
            try:
                color = discord.Color(int(color, 16))
            except ValueError:
                return await interaction.response.send_message("Invalid HEX value", ephemeral=True)

        query = """SELECT * FROM custom_roles
                    WHERE guild_id = $1 AND user_id = $2"""
        before = await CustomRole.fetchrow(query, interaction.guild.id, interaction.user.id)

        # Insert data if it doesn't exist
        if before is None:
            # Validate the name parameter
            if name is None:
                return await interaction.response.send_message("You don't have a custom role yet!", ephemeral=True)

            # Create and assign the role to user
            discord_role = await interaction.guild.create_role(name=name, colour=color or discord.Color.default())
            await interaction.user.add_roles(discord_role)

            query = """INSERT INTO custom_roles (user_id, guild_id, role_id, name, color)
                            VALUES ($1, $2, $3, $4, $5)
                         RETURNING *"""
            record = await CustomRole.fetchrow(
                query,
                interaction.user.id,
                interaction.guild.id,
                discord_role.id,
                discord_role.name,
                str(discord_role.color),
            )
            # Persist the role
            self.bot.dispatch(
                "persist_roles", guild_id=interaction.guild.id, user_id=interaction.user.id, role_ids=[discord_role.id]
            )
            # Log the role
            self.bot.dispatch("custom_role_create", data=record)

            return await interaction.response.send_message(
                embed=self.role_embed("**Custom Role has been assigned**", interaction.user, discord_role),
                ephemeral=True,
            )

        # Return role information if no parameter is passed
        if not name and not color:
            return await interaction.response.send_message(
                embed=self.role_embed("Custom Role for", interaction.user, interaction.guild.get_role(before.role_id)),
                ephemeral=True,
            )

        # Editing the role
        await interaction.guild.get_role(before.role_id).edit(
            name=name or before.name,
            colour=color or discord.Color(int(before.color.lstrip("#"), 16)),
        )

        # Update data in DB
        query = """UPDATE custom_roles
                      SET name = $4, color = $5
                    WHERE guild_id = $1 AND user_id = $2 AND role_id = $3
                RETURNING *"""
        after = await CustomRole.fetchrow(
            query, interaction.guild.id, interaction.user.id, before.role_id, name, color or before.color
        )
        self.bot.dispatch("custom_role_update", before, after)

        return await interaction.response.send_message(
            embed=self.role_embed(
                "**Custom Role has been updated**", interaction.user, interaction.guild.get_role(before.role_id)
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomRoles(bot=bot))
