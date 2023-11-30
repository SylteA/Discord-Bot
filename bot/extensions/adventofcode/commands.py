from discord import app_commands
from discord.ext import commands

from bot import core
from bot.extensions.adventofcode.utils import home_embed
from bot.extensions.adventofcode.views import AdventOfCodeView


class AdventOfCode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(AdventOfCodeView())

    @app_commands.command(name="advent-of-code")
    async def advent_of_code(self, interaction: core.InteractionType):
        """Returns information about the Advent of Code"""
        await interaction.response.send_message(embed=home_embed(), ephemeral=True, view=AdventOfCodeView())
