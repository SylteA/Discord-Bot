import discord
from discord import app_commands, ui
from discord.ext import commands

from bot import core


class PollModal(ui.Modal):
    name = ui.TextInput(label="Option name", placeholder="Enter poll option name", max_length=50, required=True)

    def __init__(self, var: discord.Interaction):
        self.var = var
        super().__init__(title="Poll options")

    @property
    def reactions(self):
        return {
            0: "1️⃣",
            1: "2️⃣",
            2: "3️⃣",
            3: "4️⃣",
            4: "5️⃣",
            5: "6️⃣",
            6: "7️⃣",
            7: "8️⃣",
            8: "9️⃣",
            9: "🔟",
        }

    async def on_submit(self, interaction: discord.Interaction) -> None:
        message = await self.var.followup.fetch_message(self.var.message.id)

        # Determine the emoji to use based on the number of options
        num = str(message.embeds[0].description).count("\n\n")
        message.embeds[0].description += f"\n\n{str(self.reactions[num])}  {self.name}"

        await message.edit(embed=message.embeds[0])
        await interaction.response.defer()


class Buttons(ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @property
    def reactions(self):
        return {
            0: "1️⃣",
            1: "2️⃣",
            2: "3️⃣",
            3: "4️⃣",
            4: "5️⃣",
            5: "6️⃣",
            6: "7️⃣",
            7: "8️⃣",
            8: "9️⃣",
            9: "🔟",
        }

    @discord.ui.button(label="Add Choice", style=discord.ButtonStyle.gray, emoji="➕")
    async def add_choice(self, interaction: discord.Interaction, _button: ui.Button):
        # Count the number of options
        num = str(interaction.message.embeds[0].description).count("\n\n")
        # If there are more than 10 options, return
        if num >= 10:
            return await interaction.response.send_message(
                "You can't make a poll with more than 10 choices", ephemeral=True
            )

        modal = PollModal(var=interaction)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remove Choice", style=discord.ButtonStyle.gray, emoji="➖")
    async def remove_choice(self, interaction: discord.Interaction, _button: ui.Button):
        embed = interaction.message.embeds[0]

        # If there are no options, return
        if str(embed.description).count("\n\n") == 0:
            return await interaction.response.send_message(
                "You can't remove a choice from a poll with no choices", ephemeral=True
            )

        # Remove the last option
        embed.description = "\n\n".join(embed.description.split("\n\n")[:-1])
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Create Poll", style=discord.ButtonStyle.gray, emoji="📝")
    async def create_poll(self, interaction: discord.Interaction, _button: ui.Button):
        # Get the embed
        embed = interaction.message.embeds[0]

        # If there are less than 2 options, return
        if str(embed.description).count("\n\n") < 2:
            return await interaction.response.send_message("You can't create a poll with no choices", ephemeral=True)

        message = await interaction.channel.send(embed=embed)

        # Add reactions
        for i in range(0, str(embed.description).count("\n\n")):
            await message.add_reaction(self.reactions[i])

        # Delete the original message
        await interaction.response.defer()
        await interaction.delete_original_response()


class Polls(commands.GroupCog, group_name="poll"):
    def __init__(self, bot: commands.AutoShardedBot):
        self.__bot = bot

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

    @app_commands.command()
    @app_commands.checks.cooldown(1, 10)
    async def new(self, interaction: core.InteractionType, desc: str):
        """Create a new poll"""

        embed = discord.Embed(
            description=f"**{desc}**\n\n",
            timestamp=discord.utils.utcnow(),
            color=discord.colour.Color.gold(),
        )
        embed.set_footer(text=f"Poll by {str(interaction.user.display_name)}")
        await interaction.response.send_message(embed=embed, ephemeral=True, view=Buttons())

    @app_commands.command()
    async def show(self, interaction: core.InteractionType, message: str, ephemeral: bool = True):
        """Show a poll result"""
        try:
            *_, channel_id, msg_id = message.split("/")

            try:
                channel = self.__bot.get_channel(int(channel_id))
                message = await channel.fetch_message(int(msg_id))
            except Exception:
                return await interaction.response.send_message("Please provide the message ID/link for a valid poll")
        except Exception:
            try:
                message = await interaction.channel.fetch_message(int(message))
            except Exception:
                return await interaction.response.send_message("Please provide the message ID/link for a valid poll")

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

        return await interaction.response.send_message("Please provide the message ID/link for a valid poll")


async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot=bot))
