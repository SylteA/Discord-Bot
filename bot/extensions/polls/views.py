import discord
from discord import ui


class PollModal(ui.Modal):
    name = ui.TextInput(label="Choice name", placeholder="Enter poll choice", max_length=50, required=True)

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


class PollButtons(ui.View):
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
        embed = interaction.message.embeds[0]

        # If there are less than 2 options, return
        if str(embed.description).count("\n\n") < 2:
            return await interaction.response.send_message(
                "You can't create a poll with less than 2 choices", ephemeral=True
            )

        message = await interaction.channel.send(embed=embed)

        # Add reactions
        for i in range(0, str(embed.description).count("\n\n")):
            await message.add_reaction(self.reactions[i])

        # Delete the original message
        await interaction.response.defer()
        await interaction.delete_original_response()
