import inspect
import types

from discord import app_commands
from discord.ext import commands

from bot import core
from utils import paginate
from utils.transformers import CommandTransformer


class GitHub(commands.Cog):
    base_url = "https://github.com/SylteA/Discord-Bot"

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @app_commands.command()
    async def source(
        self,
        interaction: core.InteractionType,
        command: app_commands.Transform[app_commands.Command, CommandTransformer(groups=False)] = None,
    ):
        """Get the source code for the bot or specified command."""
        if command is None:
            return await interaction.response.send_message(self.base_url)

        callback = getattr(command, "_callback")
        source = inspect.getsource(callback)

        # TODO: Paginate result?
        max_page_size = 1000

        first_page = next(paginate.by_lines(source, max_page_size=max_page_size))
        first_page = first_page.replace("`", "`\u200b")

        title = f"# Source code for command: [/{command.qualified_name}](<{self.get_github_url(callback)}>)"
        response = f"{title}\n```py\n{first_page}"

        response += "\n```"

        if len(source) > max_page_size:
            response += "\n### Result was truncated, view github for full source."

        return await interaction.response.send_message(response)

    def get_github_url(self, callback: types.FunctionType) -> str:
        lines, first_line = inspect.getsourcelines(callback.__code__)

        builder = [self.base_url, "blob", "master"]
        builder.extend(callback.__module__.split("."))
        builder[-1] += ".py"

        builder.append(f"#L{first_line}-L{first_line + len(lines)-1}")

        return "/".join(builder)
