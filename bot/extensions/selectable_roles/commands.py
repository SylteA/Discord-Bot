from typing import List

import discord
from discord import app_commands
from discord.ext import commands
from pydantic import BaseModel

from bot import core
from bot.models import SelectableRole


class Role(BaseModel):
    name: str
    id: int


class SelectableRoleCommands(commands.Cog):
    admin_commands = app_commands.Group(
        name="selectable-roles",
        description="Commands for managing selectable roles",
        default_permissions=discord.Permissions(administrator=True),
        guild_only=True,
    )

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.roles: dict[int, list[Role]] = {}

    def update_roles(self, guild_id: int, data: tuple[str, int]) -> None:
        if self.roles.get(guild_id):
            for role in self.roles[guild_id]:
                if role.id == data[1]:
                    return
            self.roles[guild_id].append(Role(name=data[0], id=data[1]))
        else:
            self.roles[guild_id] = [Role(name=data[0], id=data[1])]

    async def cog_load(self) -> None:
        query = "SELECT * FROM selectable_roles"
        records = await SelectableRole.fetch(query)

        for record in records:
            self.update_roles(record.guild_id, (record.role_name, record.role_id))

    async def role_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        if not self.roles.get(interaction.guild.id):
            return []

        return [
            app_commands.Choice(name=role.name, value=str(role.id))
            for role in self.roles[interaction.guild.id]
            if current.lower() in role.name.lower()
        ][:25]

    @app_commands.command(name="get-role")
    @app_commands.guild_only()
    @app_commands.autocomplete(role=role_autocomplete)
    async def get(
        self,
        interaction: core.InteractionType,
        role: str,
    ):
        """Get the selected role"""

        if not self.roles.get(interaction.guild.id) or not role.isdigit():
            return await interaction.response.send_message("That role isn't selectable!", ephemeral=True)

        role = interaction.guild.get_role(int(role))
        if role is None or not any(role.id == role_.id for role_ in self.roles[interaction.guild.id]):
            return await interaction.response.send_message("That role isn't selectable!", ephemeral=True)

        await interaction.user.add_roles(role, reason="Selectable role")

        to_remove = []
        for role_ in self.roles[interaction.guild.id]:
            if role_.id != role.id:
                to_remove.append(interaction.guild.get_role(role_.id))
        await interaction.user.remove_roles(*to_remove, reason="Selectable role")

        await interaction.response.send_message(f"Successfully added {role.mention} to you!", ephemeral=True)

    @admin_commands.command()
    async def add(
        self,
        interaction: core.InteractionType,
        role: discord.Role,
    ):
        """Add a selectable role to the database"""

        if not role.is_assignable():
            return await interaction.response.send_message(
                "That role is non-assignable by the bot. Please ensure the bot has the necessary permissions.",
                ephemeral=True,
            )

        await SelectableRole.ensure_exists(interaction.guild.id, role.id, role.name)
        self.update_roles(interaction.guild.id, (role.name, role.id))
        await interaction.response.send_message(f"Successfully added {role.mention} to the database!", ephemeral=True)

    @admin_commands.command()
    @app_commands.autocomplete(role=role_autocomplete)
    async def remove(
        self,
        interaction: core.InteractionType,
        role: str,
    ):
        """Remove a selectable role from the database"""

        if not self.roles.get(interaction.guild.id):
            return await interaction.response.send_message("There are no selectable roles!", ephemeral=True)

        role = interaction.guild.get_role(int(role))
        query = "DELETE FROM selectable_roles WHERE guild_id = $1 AND role_id = $2"
        await SelectableRole.execute(query, interaction.guild.id, role.id)

        for i, role_ in enumerate(self.roles[interaction.guild.id]):
            if role_.id == role.id:
                del self.roles[interaction.guild.id][i]
                break

        await interaction.response.send_message(
            f"Successfully removed {role.mention} from the database!", ephemeral=True
        )

    @admin_commands.command()
    async def list(
        self,
        interaction: core.InteractionType,
    ):
        """List all selectable roles"""

        if not self.roles.get(interaction.guild.id):
            return await interaction.response.send_message("There are no selectable roles!", ephemeral=True)

        roles = [f"<@&{role.id}>" for role in self.roles[interaction.guild.id]]
        embed = discord.Embed(title="Selectable roles", description="\n".join(roles), color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)
