import logging

import discord
from aiohttp import ContentTypeError
from codingame.http import HTTPError
from discord import app_commands
from discord.app_commands import Cooldown
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.clashofcode.utils import coc_client, coc_helper
from bot.extensions.clashofcode.views import CocMessageView, CreateCocView

log = logging.getLogger(__name__)


def new_coc_cooldown(interaction: discord.Interaction) -> Cooldown | None:
    """Dynamic cooldown for the /coc new command."""
    if settings.moderation.staff_role_id in [role.id for role in interaction.user.roles]:
        return None
    return Cooldown(1, 60 * 15)


@app_commands.default_permissions(administrator=True)
class ClashOfCode(commands.GroupCog, group_name="coc"):
    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        self.bot.add_view(CocMessageView())

    async def cog_load(self):
        await coc_client.login(remember_me_cookie=settings.coc.session_cookie)

    async def interaction_check(self, interaction: core.InteractionType):
        if interaction.channel_id != settings.coc.channel_id:
            await interaction.response.send_message(
                "You need to be in the Clash Of Code channel to use this command", ephemeral=True
            )
            return False
        return True

    coc_session = app_commands.Group(name="session", description="Session commands")

    @coc_session.command()
    @app_commands.checks.dynamic_cooldown(
        new_coc_cooldown, key=lambda i: settings.moderation.staff_role_id in [role.id for role in i.user.roles]
    )
    async def new(self, interaction: core.InteractionType):
        """Creates a new Clash of Code session."""
        if coc_helper.session:
            return await interaction.response.send_message("A session is already active.", ephemeral=True)

        await interaction.response.defer()

        coc_helper.session = True
        coc_helper.host = interaction.user

        role = interaction.guild.get_role(settings.coc.session_role_id)
        if not role:
            coc_helper.session = False
            coc_helper.host = None
            return await interaction.followup.send("The session role could not be found.", ephemeral=True)

        try:
            await interaction.user.add_roles(role)
        except discord.HTTPException as e:
            log.error(f"Failed to add role to {interaction.user.display_name}", exc_info=e)

        ping_role = interaction.guild.get_role(settings.coc.role_id)

        view = CocMessageView()
        msg = await interaction.followup.send(
            (
                f"**Hey, {ping_role.mention}, {interaction.user.mention} is hosting a Clash Of Code session!**\n"
                f"Everyone else can join the session to get pinged!"
            ),
            allowed_mentions=discord.AllowedMentions(roles=True, users=True),
            view=view,
        )
        coc_helper.message = msg

    @coc_session.command()
    async def end(self, interaction: core.InteractionType):
        """Ends the current coc session"""

        if not coc_helper.session:
            return await interaction.response.send_message("There is no active clash of code session", ephemeral=True)

        staff_role = interaction.guild.get_role(settings.moderation.staff_role_id)
        is_staff = staff_role in interaction.user.roles

        if coc_helper.host != interaction.user and not is_staff:
            return await interaction.response.send_message(
                "Only the session host or a staff member can end the session.", ephemeral=True
            )

        await interaction.response.defer()

        if coc_helper.message:
            try:
                view = CocMessageView()
                button = discord.utils.get(view.children, custom_id=CocMessageView.JOIN_LEAVE_CUSTOM_ID)
                button.disabled = True
                await coc_helper.message.edit(view=view)
            except discord.HTTPException as e:
                log.error("Failed to edit message to disable button", exc_info=e)

        session_role = interaction.guild.get_role(settings.coc.session_role_id)
        if session_role:
            for member in session_role.members:
                try:
                    await member.remove_roles(session_role)
                except discord.HTTPException as e:
                    log.error(f"Failed to remove role from {member.display_name}", exc_info=e)

        coc_helper.last_clash = 0
        coc_helper.session = False
        coc_helper.clash = None
        coc_helper.message = None
        coc_helper.host = None
        coc_helper.languages = None
        coc_helper.modes = None
        coc_helper.handle = None

        await interaction.followup.send(
            f"Clash session has been closed by {interaction.user.mention}. See you later",
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    coc_game = app_commands.Group(name="game", description="Game commands")

    @coc_game.command()
    async def create(self, interaction: core.InteractionType):
        """Creates a new Clash of Code game."""

        if not coc_helper.session:
            return await interaction.response.send_message(
                "There is no active clash of code session. Do `/coc session new` to start one.", ephemeral=True
            )

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

    @coc_game.command()
    async def start(self, interaction: core.InteractionType):
        """Starts the current clash game"""

        if not coc_helper.handle:
            return await interaction.response.send_message("There is no active clash of code game", ephemeral=True)

        if coc_helper.clash.started:
            return await interaction.response.send_message("The clash has already started", ephemeral=True)

        await interaction.response.defer()

        try:
            await coc_client.request(
                "ClashOfCode", "startClashByHandle", [coc_client.codingamer.id, coc_helper.clash.public_handle]
            )
        except HTTPError as e:
            log.info("Handled error in /coc start : %s\n%s", e.reason, e.data)
            return await interaction.followup.send_message(
                "An error occurred while starting the clash. Please try again later", ephemeral=True
            )
        except ContentTypeError:
            # Issue with the codingame library always assuming the response is JSON
            pass

        await interaction.followup.send_message(
            "Clash started!",
            ephemeral=True,
        )

    async def cog_app_command_error(self, interaction: core.InteractionType, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            if seconds < 60:
                time_str = f"{seconds} second{'s' if seconds != 1 else ''}"
            else:
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                if remaining_seconds > 0:
                    time_str += f" and {remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"

            await interaction.response.send_message(
                f"This command is on cooldown. Please try again in {time_str}.",
                ephemeral=True,
            )
        else:
            raise error


async def setup(bot: core.DiscordBot):
    await bot.add_cog(ClashOfCode(bot=bot))
