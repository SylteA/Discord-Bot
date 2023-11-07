import asyncio
import logging
import time

import discord
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

    @discord.ui.button(label="Select All", style=discord.ButtonStyle.blurple, emoji="🟢", custom_id=SELECT_ALL_CUSTOM_ID)
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
        label="Create Clash of Code", style=discord.ButtonStyle.green, emoji="📝", custom_id=CREATE_CUSTOM_ID, row=3
    )
    async def create_coc(self, interaction: core.InteractionType, _button: ui.Button):
        selected_languages = discord.utils.get(self.children, custom_id=self.LANGUAGES_CUSTOM_ID).values
        selected_modes = discord.utils.get(self.children, custom_id=self.MODES_CUSTOM_ID).values

        if len(selected_languages) == 25:
            selected_languages = []
        if not selected_modes:
            selected_modes = modes

        await interaction.response.defer()
        await interaction.delete_original_response()

        data = await coc_client.request(
            "ClashOfCode",
            "createPrivateClash",
            [coc_client.codingamer.id, selected_languages, selected_modes],
        )
        handle = data["publicHandle"]

        # Check if it has been too long since the last clash
        if coc_helper.session and coc_helper.last_clash + 1800 < int(time.time()):
            coc_helper.session = False

        await interaction.channel.send(
            (
                f"**Hey, {interaction.user.mention} is hosting a Clash Of Code game!**\n"
                f"Mode{'s' if len(selected_modes) > 1 else ''}: {', '.join(selected_modes).title()}\n"
                f"Programming languages: {', '.join(selected_languages) if selected_languages else 'All'}\n"
                f"Join here: <https://www.codingame.com/clashofcode/clash/{handle}>\n"
                f"{f'<@&{settings.coc.role_id}>' if not coc_helper.session else ''}"
            ),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )

        coc_helper.session = True
        coc_helper.last_clash = time.time()

        clash = await coc_client.get_clash_of_code(handle)
        coc_helper.clash = clash
        while not clash.started:
            await asyncio.sleep(10)  # wait 10s to avoid flooding the API
            clash = await coc_client.get_clash_of_code(handle)

        players = [player.pseudo for player in clash.players]
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
                # Submit an empty solution to not hold up the clash once everyone has submitted
                await coc_client.request(
                    "TestSession",
                    "submit",
                    [
                        test_session_handle,
                        {
                            "code": "",
                            "programmingLanguageId": language,
                        },
                        None,
                    ],
                )
            except HTTPError as e:
                log.error(f"Failed to submit solution to {handle}:", exc_info=e)

        while not clash.finished:
            await asyncio.sleep(10)  # wait 10s to avoid flooding the API
            clash = await coc_client.get_clash_of_code(handle)

            if len(clash.players) != len(players):
                players = [player.pseudo for player in clash.players]
                await start_message.edit(embed=em(clash.mode, ", ".join(players)))

        embed = discord.Embed(
            title="**Clash finished**",
            description="\n".join(
                ["Results:"]
                + [
                    f"{p.rank}. {p.pseudo} ("
                    + (f"Code length: {p.code_length}, " if clash.mode == "SHORTEST" else "")
                    + f"Score: {p.score}%, Time: {p.duration.seconds // 60}:{p.duration.seconds % 60:02})"
                    for p in sorted(clash.players, key=lambda p: p.rank)
                ]
            ),
        )

        await interaction.channel.send(embed=embed)
