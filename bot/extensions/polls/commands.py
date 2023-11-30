import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.extensions.polls.utils import emojis, poll_check
from bot.extensions.polls.views import PollView
from utils.transformers import MessageTransformer


class Polls(commands.GroupCog, group_name="poll"):
    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.bot.add_view(PollView())

    @app_commands.command()
    @app_commands.describe(question="Your question")
    async def new(self, interaction: core.InteractionType, question: str):
        """Create a new poll"""

        embed = discord.Embed(
            description=f"**{question}**\n\n",
            timestamp=discord.utils.utcnow(),
            color=discord.colour.Color.gold(),
        )
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True, view=PollView())

    @app_commands.command()
    async def show(
        self,
        interaction: core.InteractionType,
        message: app_commands.Transform[discord.Message, MessageTransformer],
        ephemeral: bool = True,
    ):
        """Show a poll result"""

        if not poll_check(message, self.bot.user):
            return await interaction.response.send_message("Please provide a valid poll message", ephemeral=True)

        poll_embed = message.embeds[0]
        reactions = message.reactions
        reactions_total = sum([reaction.count - 1 if str(reaction.emoji) in emojis else 0 for reaction in reactions])

        options = [field.name for field in poll_embed.fields]
        desc = poll_embed.description.split("1️")[0]

        embed = discord.Embed(
            description=desc,
            timestamp=poll_embed.timestamp,
            color=discord.Color.gold(),
        )

        for i, option in enumerate(options):
            reaction_count = reactions[i].count - 1
            indicator = "░" * 20
            if reactions_total != 0:
                indicator = "█" * int(((reaction_count / reactions_total) * 100) / 5) + "░" * int(
                    (((reactions_total - reaction_count) / reactions_total) * 100) / 5
                )

            embed.add_field(
                name=option,
                value=f"{indicator}  {int((reaction_count / (reactions_total or 1)*100))}%"
                f" (**{reaction_count} votes**)",
                inline=False,
            )

        embed.set_footer(text="Poll Result")
        return await interaction.response.send_message(embed=embed, ephemeral=ephemeral)


async def setup(bot: core.DiscordBot):
    await bot.add_cog(Polls(bot=bot))
