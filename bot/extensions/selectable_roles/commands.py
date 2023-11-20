import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.extensions.selectable_roles.views import CreateSelectableRoleView, SelectableRoleOptions
from utils.transformers import MessageTransformer


@app_commands.default_permissions(administrator=True)
class SelectableRoleCommands(commands.GroupCog, group_name="selectable-role"):
    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        # TODO: Make the view work even after a restart
        self._create_selectable_role_view = CreateSelectableRoleView(timeout=None)
        self.bot.add_view(self._create_selectable_role_view)

    @app_commands.command()
    async def create(self, interaction: core.InteractionType, title: str, channel: discord.TextChannel = None):
        """Create a new selectable role message"""

        if channel is None:
            channel = interaction.channel

        await channel.send(title, view=self._create_selectable_role_view)
        await interaction.response.send_message(
            "Successfully created selectable role message! Please add role options to it by using /selectable-role add",
            ephemeral=True,
        )

    @app_commands.command()
    async def add(
        self,
        interaction: core.InteractionType,
        message: app_commands.Transform[discord.Message, MessageTransformer],
        text: str,
        role: discord.Role,
        emoji: str,
    ):
        """Add a selectable role to a message"""

        if message.author != self.bot.user:
            return await interaction.response.send_message(
                "This message is not a selectable role message.", ephemeral=True
            )

        emoji = discord.utils.get(interaction.guild.emojis, name=emoji)
        view = discord.ui.View.from_message(message, timeout=None)
        options = []
        if view.children:
            options = view.children[0].options

        view = CreateSelectableRoleView(timeout=None)
        view.add_item(
            SelectableRoleOptions(
                options + [discord.SelectOption(label=role.name, description=text, value=str(role.id), emoji=emoji)]
            )
        )

        await message.edit(view=view)
        await interaction.response.send_message("Successfully added role to selectable role message!", ephemeral=True)

    @app_commands.command()
    async def remove(
        self,
        interaction: core.InteractionType,
        message: app_commands.Transform[discord.Message, MessageTransformer],
        role: discord.Role,
    ):
        """Remove a selectable role from a message"""

        if message.author != self.bot.user:
            return await interaction.response.send_message(
                "This message is not a selectable role message.", ephemeral=True
            )

        view = discord.ui.View.from_message(message, timeout=None)
        options = []
        if view.children:
            options = view.children[0].options
        options = [option for option in options if option.value != str(role.id)]

        if len(options) == 0:
            await message.edit(view=None)
        else:
            view = CreateSelectableRoleView(timeout=None)
            view.add_item(SelectableRoleOptions(options))
            await message.edit(view=view)

        await interaction.response.send_message(
            "Successfully removed role from selectable role message!", ephemeral=True
        )
