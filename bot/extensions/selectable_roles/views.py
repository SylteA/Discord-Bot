import discord
from discord import ui

from bot import core


class SelectableRoleOptions(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption]):
        super().__init__(
            placeholder="Select a role",
            custom_id=CreateSelectableRoleView.DROPDOWN_CUSTOM_ID,
            min_values=0,
            options=options,
        )

    async def callback(self, interaction: core.InteractionType):
        if not self.values:
            roles = [interaction.guild.get_role(int(option.value)) for option in self.options]
            await interaction.user.remove_roles(*roles, reason="Selectable role")
            return await interaction.response.send_message("Successfully removed the role from you!", ephemeral=True)

        selected_role_id = int(self.values[0])
        role = interaction.guild.get_role(selected_role_id)

        other_roles = [
            interaction.guild.get_role(int(option.value)) for option in self.options if option != selected_role_id
        ]

        await interaction.user.remove_roles(*other_roles, reason="Selectable role")
        await interaction.user.add_roles(role, reason="Selectable role")
        await interaction.response.send_message(f"Successfully added {role.mention} to you!", ephemeral=True)


class CreateSelectableRoleView(ui.View):
    DROPDOWN_CUSTOM_ID = "extensions:selectable_roles:dropdown"
