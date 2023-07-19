import typing as t

from discord import app_commands

from bot import core
from bot.extensions.readthedocs.utils import finder
from utils.errors import IgnorableException


class CommandTransformer(app_commands.Transformer):
    def __init__(self, commands: bool = True, groups: bool = True):
        self.commands = commands
        self.groups = groups

    def walk_commands(
        self, tree: app_commands.CommandTree
    ) -> t.Generator[app_commands.Command | app_commands.Group, None, None]:
        for obj in tree.walk_commands():
            if isinstance(obj, app_commands.Command) and self.commands:
                yield obj

            if isinstance(obj, app_commands.Group) and self.groups:
                yield obj

    def find_command_fuzzy(self, interaction: core.InteractionType, search: str) -> list[str]:
        return finder(
            text=search, collection=[command.qualified_name for command in self.walk_commands(interaction.client.tree)]
        )

    async def transform(self, interaction: core.InteractionType, value: str, /):
        qualified_name = value.lower()

        for command in self.walk_commands(interaction.client.tree):
            if command.qualified_name == qualified_name:
                return command

        await interaction.response.send_message("I couldn't find a command with that name", ephemeral=True)
        raise IgnorableException

    async def autocomplete(self, interaction: core.InteractionType, value: str) -> list[app_commands.Choice[str]]:
        options = self.find_command_fuzzy(interaction=interaction, search=value)
        return [app_commands.Choice(name=option, value=option) for option in options]
