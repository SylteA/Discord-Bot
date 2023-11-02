import typing as t

import discord
from discord import ui

from bot import core
from bot.extensions.polls.utils import emojis

if t.TYPE_CHECKING:
    from discord.embeds import _EmbedFieldProxy


class PollModal(ui.Modal, title="Add Choice"):
    name = ui.TextInput(label="Choice name", placeholder="Enter poll choice", max_length=32, required=True)
    description = ui.TextInput(
        label="Choice description (optional)",
        placeholder="Enter poll choice description",
        style=discord.TextStyle.long,
        max_length=512,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        embed = interaction.message.embeds[0]
        field_count = len(embed.fields)

        embed.add_field(name=f"{str(emojis[field_count])}  {self.name}", value=self.description, inline=False)
        field_count += 1
        view = CreatePollView()

        add_choice_btn = discord.utils.get(view.children, custom_id=CreatePollView.ADD_CUSTOM_ID)
        create_poll_btn = discord.utils.get(view.children, custom_id=CreatePollView.CREATE_CUSTOM_ID)
        delete_select = discord.utils.find(lambda child: isinstance(child, discord.ui.Select), view.children)

        add_choice_btn.disabled = field_count > 9
        create_poll_btn.disabled = field_count < 2

        view.remove_item(delete_select)
        if field_count >= 1:
            view.add_item(DeletePollOptions(embed.fields))

        await interaction.response.edit_message(embed=embed, view=view)


class DeletePollOptions(discord.ui.Select):
    def __init__(self, fields: list["_EmbedFieldProxy"]):
        super().__init__(
            row=2,
            max_values=len(fields),
            placeholder="➖ Select a choice to remove",
            custom_id=CreatePollView.DELETE_CUSTOM_ID,
            options=[
                discord.SelectOption(emoji=emojis[i], label=field.name.split(maxsplit=1)[1], value=str(i))
                for i, field in enumerate(fields)
            ],
        )

    async def callback(self, interaction: core.InteractionType):
        embed = interaction.message.embeds[0]

        for value in sorted(self.values, reverse=True):  # to avoid conflict
            embed.remove_field(int(value))

        for i, field in enumerate(embed.fields):
            embed.set_field_at(
                i, name=f"{emojis[i]}  {field.name.split(maxsplit=1)[1]}", value=field.value, inline=False
            )

        self.view.remove_item(self)
        if len(embed.fields) >= 1:
            self.view.add_item(DeletePollOptions(embed.fields))

        # We removed a choice so there gotta be some space for more
        add_choice_btn = discord.utils.get(self.view.children, custom_id=CreatePollView.ADD_CUSTOM_ID)
        add_choice_btn.disabled = False

        await interaction.response.edit_message(embed=embed, view=self.view)


class CreatePollView(ui.View):
    ADD_CUSTOM_ID = "extensions:polls:add"
    DELETE_CUSTOM_ID = "extensions:polls:delete"
    CREATE_CUSTOM_ID = "extensions:polls:create"

    @discord.ui.button(label="Add Choice", style=discord.ButtonStyle.blurple, emoji="➕", custom_id=ADD_CUSTOM_ID)
    async def add_choice(self, interaction: core.InteractionType, _button: ui.Button):
        embed = interaction.message.embeds[0]
        field_count = len(embed.fields)

        if field_count >= 10:
            return await interaction.response.send_message(
                "You can't make a poll with more than 10 choices", ephemeral=True
            )

        await interaction.response.send_modal(PollModal())

    @discord.ui.button(
        label="Create Poll", style=discord.ButtonStyle.green, emoji="📝", custom_id=CREATE_CUSTOM_ID, disabled=True
    )
    async def create_poll(self, interaction: core.InteractionType, _button: ui.Button):
        embed = interaction.message.embeds[0]

        if len(embed.fields) < 2:
            return await interaction.response.send_message(
                "You can't create a poll with less than 2 choices", ephemeral=True
            )

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for i in range(0, len(embed.fields)):
            await message.add_reaction(emojis[i])
