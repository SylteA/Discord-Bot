import logging
import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.config import settings

log = logging.getLogger(__name__)


class ChallengeCommands(commands.GroupCog, group_name="challenges"):
    """Commands for weekly challenges in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    async def interaction_check(self, interaction: core.InteractionType) -> bool:
        """Verify that the caller has one of the provided roles"""
        valid_roles = [
            settings.moderation.staff_role_id,
            settings.challenges.host_role_id,
            settings.challenges.host_helper_role_id,
        ]

        if interaction.command.name == "submit":
            valid_roles = [settings.challenges.participant_role_id]

        member = await self.bot.guild.fetch_member(interaction.user.id)

        if member is None:
            await interaction.response.send_message(
                f"This command can only be used in the {self.bot.guild.name} server.", ephemeral=True
            )
            return False

        for role_id in valid_roles:
            role = member.get_role(role_id)

            if role is not None:
                return True

        required_roles = "\n".join(f"<@&{rid}>" for rid in valid_roles)

        await interaction.response.send_message(
            f"You do not have the required roles to use this command." f"\n\nRequired role(s):\n{required_roles}",
            ephemeral=True,
        )
        return False

    @property
    def winner_role(self) -> discord.Role | None:
        return self.bot.guild.get_role(settings.challenges.winner_role_id)

    @property
    def submitted_role(self) -> discord.Role | None:
        return self.bot.guild.get_role(settings.challenges.submitted_role_id)

    @property
    def participant_role(self) -> discord.Role | None:
        return self.bot.guild.get_role(settings.challenges.participant_role_id)

    @property
    def info_channel(self) -> discord.TextChannel | None:
        return self.bot.guild.get_channel(settings.challenges.info_channel_id)

    @property
    def submit_channel(self) -> discord.TextChannel | None:
        return self.bot.guild.get_channel(settings.challenges.submit_channel_id)

    @property
    def submissions_channel(self) -> discord.TextChannel | None:
        return self.bot.guild.get_channel(settings.challenges.submissions_channel_id)

    @property
    def games_channel(self) -> discord.TextChannel | None:
        return self.bot.guild.get_channel(settings.bot.games_channel_id)

    @app_commands.command()
    async def clear_winners(self, interaction: core.InteractionType):
        """Clears the winner role from all members that have it."""
        await interaction.response.defer(thinking=True)

        for member in self.winner_role.members:
            await member.remove_roles(self.winner_role)

        return await interaction.followup.send("Cleared winners.", ephemeral=False)

    @app_commands.command()
    @app_commands.describe(message_id="Message must be in the discussions channel.")
    async def assign_winners(self, interaction: core.InteractionType, message_id: str):
        """Assigns winners from the provided message"""
        try:
            message_id = int(message_id)
        except ValueError:
            return await interaction.response.send_message("Failed to convert message_id to integer.")

        await interaction.response.defer(thinking=True)

        try:
            message = await self.bot.http.get_message(
                channel_id=settings.challenges.discussion_channel_id, message_id=int(message_id)
            )
            description = message["embeds"][0]["description"]
        except (discord.HTTPException, KeyError, IndexError) as e:
            return await interaction.response.send_message(
                f"Failed to get the description of that message! {type(e).__name__}"
            )

        user_id_pattern = re.compile(r"<@!?(\d+)>")

        failed: dict[str, str] = {}

        for user_id in re.findall(user_id_pattern, description):
            try:
                member = await self.bot.guild.fetch_member(int(user_id))
            except discord.NotFound:
                failed[user_id] = "NotFound"
            except discord.HTTPException:
                failed[user_id] = "HTTPException"
            else:
                await member.add_roles(self.winner_role)

        # TODO: Create embed for this with button to show failed users instead of showing everything in the same message
        output = "Assigned winners!"

        if failed:
            output += "\n\nThese users failed though...\n\n"
            output += "\n".join(f"{user_id}: {reason}" for user_id, reason in failed.items())

        return await interaction.followup.send(output)

    @app_commands.command()
    @app_commands.describe(member="Member to remove role from.")
    async def resubmit(self, interaction: core.InteractionType, member: discord.Member):
        """Remove the submitted role from the specified member."""

        if self.submitted_role in member.roles:
            await member.remove_roles(self.submitted_role)
            return await interaction.response.send_message(f"Removed submitted role from {member.display_name}")

        return await interaction.response.send_message(f"{member.display_name} does not have that role!")

    @app_commands.command()
    @app_commands.checks.cooldown(rate=1, per=3600)
    async def announce(self, interaction: core.InteractionType):
        """Send an announcement in the info channel mentioning the winners."""

        text = (
            f"{self.winner_role.mention} 🥞 have been given out, go deposit them in {self.games_channel.mention}."
            f"\nAnalysis for the challenge will be available shortly in {self.info_channel.mention}."
        )
        await self.info_channel.send(text, allowed_mentions=discord.AllowedMentions(roles=[self.winner_role]))

        return await interaction.response.send_message("Announcement sent.")

    @app_commands.command()
    @app_commands.checks.cooldown(rate=1, per=3600)
    async def open(self, interaction: core.InteractionType):
        """Open the submission channel."""
        role = self.bot.guild.default_role

        overwrites = self.submit_channel.overwrites_for(role)
        overwrites.update(send_message=None)

        await self.submit_channel.set_permissions(role, overwrite=overwrites)

        text = (
            f"{self.participant_role.mention} Submissions are open! "
            f"Use the /{self.submit.qualified_name} command to submit your solution!."
        )

        await self.info_channel.send(text, allowed_mentions=discord.AllowedMentions(roles=[self.participant_role]))
        return await interaction.response.send_message("Submissions opened.")

    @app_commands.command()
    @app_commands.checks.cooldown(rate=1, per=3600)
    async def close(self, interaction: core.InteractionType):
        """Close the submission channel."""
        role = self.bot.guild.default_role

        overwrites = self.submit_channel.overwrites_for(role)
        overwrites.update(send_message=False)

        await self.submit_channel.set_permissions(role, overwrite=overwrites)

        text = (
            f"{self.participant_role.mention} Submissions are closed. "
            f"Testing will begin soon. See you in the next challenge"
        )
        await self.info_channel.send(text, allowed_mentions=discord.AllowedMentions(roles=[self.participant_role]))
        return await interaction.response.send_message("Submissions closed.")

    @app_commands.command()
    @app_commands.describe(attachment="Your code file.")
    async def submit(self, interaction: core.InteractionType, attachment: discord.Attachment):
        """Submit your code."""
        overwrites = self.submit_channel.overwrites_for(self.bot.guild.default_role)
        if overwrites.send_messages is not None and not overwrites.send_messages:
            return await interaction.response.send_message(
                "Submissions are not open, they typically open a day after the challenge drops.", ephemeral=True
            )

        if self.submitted_role in interaction.user.roles:
            return await interaction.response.send_message(
                "You have already submitted a solution for this challenge!", ephemeral=True
            )

        filetype = attachment.filename.split(".")[-1]
        if len(filetype) > 4 or len(filetype) == 0:
            return await interaction.response.send_message(
                "File extension must be between 1 and 4 characters.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True, thinking=True)

        code = (await attachment.read()).decode("u8")
        log.info(len(code) == attachment.size)

        content = f"```{filetype}\n" + code.replace("`", "\u200b`") + "```"
        if len(content) > 4096:
            # 4096 = max embed description size
            max_user_length = 4096 - len(filetype) - 7
            msg = f"Your submission can't be __more than {max_user_length} characters__."

            return await interaction.followup.send(msg, ephemeral=True)

        await interaction.user.add_roles(self.submitted_role)

        embed = discord.Embed(description=content, color=0x36393E, timestamp=datetime.utcnow())
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"#ID: {interaction.user.id} • {len(code)} chars • Language: {filetype}")
        await self.submissions_channel.send(embed=embed)

        embed.set_author(name="Your submission", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"{len(code)} chars • Language: {filetype}")
        return await interaction.followup.send(embed=embed, ephemeral=True)
