import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.extensions.polls.views import PollButtons
from utils.transformers import MessageTransformer


class Polls(commands.GroupCog, group_name="poll"):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @property
    def reactions(self):
        return {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
        }

    def poll_check(self, message: discord.Message):
        try:
            embed = message.embeds[0]
        except Exception:
            return False
        if str(embed.footer.text).count("Poll by") == 1:
            return message.author == self.bot.user
        return False

    @app_commands.command()
    @app_commands.describe(question="Your question")
    async def new(self, interaction: core.InteractionType, question: str):
        """Create a new poll"""

        embed = discord.Embed(
            description=f"**{question}**\n\n",
            timestamp=discord.utils.utcnow(),
            color=discord.colour.Color.gold(),
        )
        embed.set_footer(text=f"Poll by {str(interaction.user.display_name)}")
        await interaction.response.send_message(embed=embed, ephemeral=True, view=PollButtons())

    @app_commands.command()
    async def show(
        self,
        interaction: core.InteractionType,
        message: app_commands.Transform[discord.Message, MessageTransformer],
        ephemeral: bool = True,
    ):
        """Show a poll result"""

        if self.poll_check(message):
            poll_embed = message.embeds[0]
            reactions = message.reactions
            reactions_total = sum(
                [reaction.count - 1 if str(reaction.emoji) in self.reactions.values() else 0 for reaction in reactions]
            )

            options = list(
                map(
                    lambda o: " ".join(o.split()[1:]),
                    poll_embed.description.split("1️")[1].split("\n\n"),
                )
            )
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

        return await interaction.response.send_message("Please provide a valid poll message", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot=bot))
