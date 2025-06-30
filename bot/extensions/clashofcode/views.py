import asyncio
import logging
import time

import discord
from aiohttp import ContentTypeError
from codingame.http import HTTPError
from discord import ui

from bot import core
from bot.config import settings
from bot.extensions.clashofcode.utils import coc_client, coc_helper, languages, modes

log = logging.getLogger(__name__)


def em(mode: str, players: str):
    embed = discord.Embed(title="**Clash started**")
    embed.add_field(name="Mode", value=mode.title(), inline=False)
    embed.add_field(name="Players", value=players)
    return embed


async def resolve_member(guild: discord.Guild, name: str) -> discord.Member | None:
    """Case-insensitive search for a member in a guild by name or display name."""
    return discord.utils.find(
        lambda m: m.display_name.lower() == name.lower() or m.name.lower() == name.lower(), guild.members
    )


class CocMessageView(ui.View):
    JOIN_LEAVE_CUSTOM_ID = "extensions:clashofcode:join_leave"
    CREATE_GAME_CUSTOM_ID = "extensions:clashofcode:create_game"

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Join/Leave Session",
        style=discord.ButtonStyle.primary,
        custom_id=JOIN_LEAVE_CUSTOM_ID,
    )
    async def join_leave_session(self, interaction: core.InteractionType, button: ui.Button):
        if not coc_helper.session:
            button.disabled = True
            await interaction.response.edit_message(view=self)
            return await interaction.followup.send("This clash of code session has already ended.", ephemeral=True)

        role = coc_helper.session_role
        if not role:
            await interaction.response.send_message("The session role could not be found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            try:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message("You have left the session.", ephemeral=True)
            except discord.HTTPException:
                await interaction.response.send_message("Failed to leave the session.", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("You have joined the session.", ephemeral=True)
            except discord.HTTPException:
                await interaction.response.send_message("Failed to join the session.", ephemeral=True)

    @discord.ui.button(
        label="Create Game",
        style=discord.ButtonStyle.success,
        custom_id=CREATE_GAME_CUSTOM_ID,
    )
    async def create_game(self, interaction: core.InteractionType, button: ui.Button):
        is_staff = settings.moderation.staff_role_id in [role.id for role in interaction.user.roles]
        if interaction.user != coc_helper.host and not is_staff:
            return await interaction.response.send_message(
                "Only the session host or a staff member can create a game.", ephemeral=True
            )

        if coc_helper.handle:
            return await interaction.response.send_message(
                "A game has already been created for this session.", ephemeral=True
            )

        await interaction.response.send_message(
            "Select the programming languages and modes you want to use for the game",
            ephemeral=True,
            view=CreateCocView(),
        )


class CreateCocView(ui.View):
    LANGUAGES_CUSTOM_ID = "extensions:clashofcode:languages"
    MODES_CUSTOM_ID = "extensions:clashofcode:modes"
    SELECT_ALL_CUSTOM_ID = "extensions:clashofcode:select_all"
    DESELECT_ALL_CUSTOM_ID = "extensions:clashofcode:deselect_all"
    CREATE_CUSTOM_ID = "extensions:clashofcode:create"

    @discord.ui.select(
        custom_id=LANGUAGES_CUSTOM_ID,
        placeholder="➕ Select a language",
        options=[discord.SelectOption(label=lang, default=True) for lang in languages],
        max_values=len(languages),
    )
    async def select_languages(self, interaction: core.InteractionType, _select: ui.Select):
        await interaction.response.defer()

    @discord.ui.button(
        label="Select All", style=discord.ButtonStyle.blurple, emoji="🟢", custom_id=SELECT_ALL_CUSTOM_ID
    )
    async def select_all_languages(self, interaction: core.InteractionType, _button: ui.Button):
        modes_select = discord.utils.get(self.children, custom_id=self.MODES_CUSTOM_ID)
        for option in modes_select.options:
            option.default = not modes_select.values or option.label in modes_select.values

        await interaction.response.edit_message(view=self)

        for option in modes_select.options:
            option.default = True

    @discord.ui.button(
        label="Deselect All", style=discord.ButtonStyle.blurple, emoji="🔴", custom_id=DESELECT_ALL_CUSTOM_ID
    )
    async def deselect_all_languages(self, interaction: core.InteractionType, _button: ui.Button):
        languages_select = discord.utils.get(self.children, custom_id=self.LANGUAGES_CUSTOM_ID)
        modes_select = discord.utils.get(self.children, custom_id=self.MODES_CUSTOM_ID)
        for option in languages_select.options:
            option.default = False
        for option in modes_select.options:
            option.default = not modes_select.values or option.label in modes_select.values

        await interaction.response.edit_message(view=self)

        for option in languages_select.options:
            option.default = True
        for option in modes_select.options:
            option.default = True

    @discord.ui.select(
        custom_id=MODES_CUSTOM_ID,
        placeholder="➕ Select a mode",
        options=[discord.SelectOption(label=mode, default=True) for mode in modes],
        max_values=len(modes),
    )
    async def select_modes(self, interaction: core.InteractionType, _select: ui.Select):
        await interaction.response.defer()

    @discord.ui.button(
        label="Create Game", style=discord.ButtonStyle.green, emoji="📝", custom_id=CREATE_CUSTOM_ID, row=3
    )
    async def create_coc(self, interaction: core.InteractionType, _button: ui.Button):
        is_staff = settings.moderation.staff_role_id in [role.id for role in interaction.user.roles]
        if interaction.user != coc_helper.host and not is_staff:
            return await interaction.response.send_message(
                "Only the session host or a staff member can create a game.", ephemeral=True
            )

        selected_languages = discord.utils.get(self.children, custom_id=self.LANGUAGES_CUSTOM_ID).values
        selected_modes = discord.utils.get(self.children, custom_id=self.MODES_CUSTOM_ID).values

        if len(selected_languages) == 25:
            selected_languages = []
        if not selected_modes:
            selected_modes = modes

        await interaction.response.defer(thinking=True)
        await interaction.delete_original_response()

        # A session already exists, and it was recently created
        if coc_helper.session and coc_helper.last_clash + 60 * 5 > int(time.time()):
            await interaction.followup.send("A session has already been made!", ephemeral=True)
            return

        data = await coc_client.request(
            "ClashOfCode",
            "createPrivateClash",
            [coc_client.codingamer.id, selected_languages, selected_modes],
        )
        handle = data["publicHandle"]
        coc_helper.handle = handle

        msg = await interaction.channel.send(
            (
                f"**Hey, {interaction.user.mention} is hosting a Clash Of Code game!**\n"
                f"Mode{'s' if len(selected_modes) > 1 else ''}: {', '.join(selected_modes).title()}\n"
                f"Programming languages: {', '.join(selected_languages) if selected_languages else 'All'}\n"
                f"Join here: <https://www.codingame.com/clashofcode/clash/{handle}>\n"
                f"<@&{settings.coc.session_role_id}>"
            ),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        coc_helper.session = True
        coc_helper.last_clash = time.time()

        clash = await coc_client.get_clash_of_code(handle)
        coc_helper.clash = clash

        tries = 45
        while not clash.started and tries > 0:
            await asyncio.sleep(10)  # wait 10s to avoid flooding the API
            clash = await coc_client.get_clash_of_code(handle)
            tries -= 1

        if not clash.started:
            coc_helper.clash = None
            coc_helper.handle = None
            await msg.reply("Canceling clash due to lack of participants.", view=CocMessageView())

            try:
                await coc_client.request(
                    "ClashOfCode",
                    "leaveClashByHandle",
                    [coc_client.codingamer.id, handle],
                )
            except HTTPError as e:
                log.error(f"Failed to leave clash: {handle}", exc_info=e)
            except ContentTypeError:
                # Issue with the codingame library always assuming the response is JSON
                pass

            return

        players = [player.pseudo for player in clash.players if player.id != coc_client.codingamer.id]
        start_message = await interaction.channel.send(embed=em(clash.mode, ", ".join(players)))

        test_session_handle = None
        try:
            # Get test session handle
            data = await coc_client.request("ClashOfCode", "startClashTestSession", [coc_client.codingamer.id, handle])
            test_session_handle = data["handle"]
        except HTTPError as e:
            log.error(f"Failed to start test session for {handle}:", exc_info=e)

        if test_session_handle:
            if selected_languages:
                language = selected_languages[0]
            else:
                language = "Python3"

            try:
                # Submit a solution to not hold up the clash once everyone has submitted
                await coc_client.request(
                    "TestSession",
                    "submit",
                    [
                        test_session_handle,
                        {
                            "code": "Ignore me, I am just a bot.",
                            "programmingLanguageId": language,
                        },
                        None,
                    ],
                )
                await coc_client.request(
                    "ClashOfCode",
                    "shareCodinGamerSolutionByHandle",
                    [coc_client.codingamer.id, handle],
                )
            except HTTPError as e:
                log.error(f"Failed to submit solution to {handle}:", exc_info=e)
            except ContentTypeError:
                # Issue with the codingame library always assuming the response is JSON
                pass

        while not clash.finished:
            await asyncio.sleep(10)  # wait 10s to avoid flooding the API
            clash = await coc_client.get_clash_of_code(handle)

            if len(clash.players) - 1 != len(players):  # -1 for the bot
                players = [player.pseudo for player in clash.players if player.id != coc_client.codingamer.id]
                await start_message.edit(embed=em(clash.mode, ", ".join(players)))

        coc_helper.clash = None
        coc_helper.handle = None
        coc_helper.session = False

        embed = discord.Embed(
            title="**Clash finished**",
            description="\n".join(
                ["Results:"]
                + [
                    f"{p.rank}. {p.pseudo} ("
                    + (f"Code length: {p.code_length}, " if clash.mode == "SHORTEST" else "")
                    + f"Score: {p.score}%, Time: {p.duration.seconds // 60}:{p.duration.seconds % 60:02})"
                    for p in sorted(clash.players, key=lambda p: p.rank)
                    if p.id != coc_client.codingamer.id
                ]
            ),
        )

        await msg.reply(embed=embed, view=CocMessageView())