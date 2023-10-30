import discord
from discord import ui


class PollModal(ui.Modal):
    name = ui.TextInput(label="Choice name", placeholder="Enter poll choice", max_length=32, required=True)
    description = ui.TextInput(
        label="Choice description (optional)",
        placeholder="Enter poll choice description",
        style=discord.TextStyle.long,
        max_length=512,
        required=False,
    )

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

        num = len(message.embeds[0].fields)
        message.embeds[0].add_field(
            name=f"{str(self.reactions[num])}  {self.name}", value=self.description, inline=False
        )

        await message.edit(embed=message.embeds[0])
        await interaction.response.defer()


class CreatePollView(ui.View):
    CREATE_CUSTOM_ID = "extensions:polls:create"
    ADD_CUSTOM_ID = "extensions:polls:add"
    SELECT_CUSTOM_ID = "extensions:polls:select"
    DELETE_CUSTOM_ID = "extensions:polls:delete"

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

    @discord.ui.button(label="Add Choice", style=discord.ButtonStyle.gray, emoji="➕", custom_id=ADD_CUSTOM_ID)
    async def add_choice(self, interaction: discord.Interaction, _button: ui.Button):
        num = len(interaction.message.embeds[0].fields)

        if num >= 10:
            return await interaction.response.send_message(
                "You can't make a poll with more than 10 choices", ephemeral=True
            )

        modal = PollModal(var=interaction)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remove Choice", style=discord.ButtonStyle.gray, emoji="➖", custom_id=DELETE_CUSTOM_ID)
    async def remove_choice(self, interaction: discord.Interaction, _button: ui.Button):
        embed = interaction.message.embeds[0]

        if len(embed.fields) == 0:
            return await interaction.response.send_message(
                "You can't remove a choice from a poll with no choices", ephemeral=True
            )

        options = []
        for i in range(0, len(embed.fields)):
            options.append(
                discord.SelectOption(label=embed.fields[i].name[4:], value=str(i + 1), emoji=self.reactions[i])
            )

        async def callback(interaction: discord.Interaction):
            embed = interaction.message.embeds[0]
            selected = int(interaction.data["values"][0])

            embed.remove_field(selected - 1)

            for x in range(0, len(embed.fields)):
                embed.set_field_at(
                    x,
                    name=f"{str(self.reactions[x])}  {embed.fields[x].name[4:]}",
                    value=embed.fields[x].value,
                    inline=False,
                )

            await interaction.response.defer()
            await interaction.edit_original_response(embed=embed, view=self)

        select = discord.ui.Select(
            placeholder="Select a choice to remove", options=options, custom_id=self.SELECT_CUSTOM_ID
        )
        select.callback = callback
        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.defer()
        await interaction.edit_original_response(embed=embed, view=view)

    @discord.ui.button(label="Create Poll", style=discord.ButtonStyle.green, emoji="📝", custom_id=CREATE_CUSTOM_ID)
    async def create_poll(self, interaction: discord.Interaction, _button: ui.Button):
        embed = interaction.message.embeds[0]

        if len(embed.fields) < 2:
            return await interaction.response.send_message(
                "You can't create a poll with less than 2 choices", ephemeral=True
            )

        message = await interaction.channel.send(embed=embed)

        for i in range(0, len(embed.fields)):
            await message.add_reaction(self.reactions[i])

        await interaction.response.defer()
        await interaction.delete_original_response()
