import discord
from discord.ext import commands

from config import (
    BOT_COMMANDS_CHANNELS_ID,
    BOT_GAMES_CHANNEL_ID,
    CHALLENGE_HIDDEN_CHANNEL_ID,
    CHALLENGE_HOST_HELPER_ROLE_ID,
    CHALLENGE_HOST_ROLE_ID,
    CHALLENGE_INFO_CHANNEL_ID,
    CHALLENGE_PARTICIPANT_ROLE_ID,
    CHALLENGE_POST_CHANNEL_ID,
    CHALLENGE_SUBMIT_CHANNEL_ID,
    CHALLENGE_SUBMITTED_ROLE_ID,
    CHALLENGE_WINNER_ROLE_ID,
    STAFF_ROLE_ID,
    TIMATHON_CHANNEL_ID,
    TIMATHON_PARTICIPANT_ROLE_ID,
)


async def setup(bot):
    await bot.add_cog(ChallengeHandler(bot))


class ChallengeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_any_role(STAFF_ROLE_ID, CHALLENGE_HOST_ROLE_ID, CHALLENGE_HOST_HELPER_ROLE_ID)
    @commands.group(name="challenges", aliases=("c",))
    async def challenges_group(self, ctx: commands.Context) -> None:
        """All of the Challenges commands"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @challenges_group.command(
        name="resubmit",
        aliases=("rs",),
        brief="Resubmit Command to remove submitted role",
    )
    async def challenges_resubmit(self, ctx: commands.Context, member: discord.Member):
        submitted_role = ctx.guild.get_role(CHALLENGE_SUBMITTED_ROLE_ID)

        if submitted_role in member.roles:
            await member.remove_roles(submitted_role)
            return await ctx.send(f"Submitted role removed from {member.mention}")

        return await ctx.send("Member doesn't have the submitted role")

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @challenges_group.command(
        name="announce_winners",
        aliases=("aw", "announce"),
        brief="Command to announce the distribution of :pancakes:",
    )
    async def announce_winners(self, ctx: commands.Context):
        info_channel = ctx.guild.get_channel(CHALLENGE_INFO_CHANNEL_ID)

        return await info_channel.send(
            f"<@&{CHALLENGE_WINNER_ROLE_ID}> :pancakes: have been given out, "
            f"go deposit them in <#{BOT_GAMES_CHANNEL_ID}>. \n"
            f"Analysis for the challenge will be available shortly in <#{CHALLENGE_INFO_CHANNEL_ID}>",
            allowed_mentions=discord.AllowedMentions(roles=[discord.Object(CHALLENGE_WINNER_ROLE_ID)]),
        )

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @challenges_group.command(
        name="open_submissions",
        aliases=("os", "open"),
        brief="Command to open submissions",
    )
    async def open_submissions(self, ctx: commands.Context):
        info_channel = ctx.guild.get_channel(CHALLENGE_INFO_CHANNEL_ID)

        submit_channel = ctx.guild.get_channel(CHALLENGE_SUBMIT_CHANNEL_ID)

        # Allows people to submit
        overwrite = submit_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await submit_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        return await info_channel.send(
            f"<@&{CHALLENGE_PARTICIPANT_ROLE_ID}> Submissions are open."
            f"Upload your code file with extension in <#{CHALLENGE_SUBMIT_CHANNEL_ID}>. "
            f"Send `t.tag submitting` in <#{BOT_COMMANDS_CHANNELS_ID[0]}> for more details",
            allowed_mentions=discord.AllowedMentions(roles=[discord.Object(CHALLENGE_PARTICIPANT_ROLE_ID)]),
        )

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @challenges_group.command(
        name="close_submissions",
        aliases=("cs", "close"),
        brief="Command to close submissions",
    )
    async def close_submissions(self, ctx: commands.Context):
        info_channel = ctx.guild.get_channel(CHALLENGE_INFO_CHANNEL_ID)

        submit_channel = ctx.guild.get_channel(CHALLENGE_SUBMIT_CHANNEL_ID)

        # Disallows people to submit
        overwrite = submit_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await submit_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        return await info_channel.send(
            f"<@&{CHALLENGE_SUBMITTED_ROLE_ID}> Submissions are closed. "
            "Testing will begin soon. See you in the next challenge",
            allowed_mentions=discord.AllowedMentions(roles=[discord.Object(CHALLENGE_SUBMITTED_ROLE_ID)]),
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Participant role.
        if payload.emoji != discord.PartialEmoji(name="🖐️"):
            return

        if payload.channel_id == CHALLENGE_POST_CHANNEL_ID:
            submitted = self.bot.guild.get_role(CHALLENGE_SUBMITTED_ROLE_ID)
            if submitted in payload.member.roles:
                return

            participant = self.bot.guild.get_role(CHALLENGE_PARTICIPANT_ROLE_ID)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

        elif payload.channel_id == TIMATHON_CHANNEL_ID:

            participant = self.bot.guild.get_role(TIMATHON_PARTICIPANT_ROLE_ID)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

    @commands.Cog.listener()
    async def on_message(self, message):  # Submitted role.

        if message.channel.id == CHALLENGE_SUBMIT_CHANNEL_ID:  # Weekly

            if message.author.id == self.bot.user.id:
                return

            if message.author.bot:
                return await message.delete()

            submitted = self.bot.guild.get_role(CHALLENGE_SUBMITTED_ROLE_ID)
            submission_channel = self.bot.guild.get_channel(CHALLENGE_HIDDEN_CHANNEL_ID)

            if submitted not in message.author.roles:
                await message.delete()
                attach = message.attachments and message.attachments[0]

                if not attach:
                    msg = (
                        f"{message.author.mention} make sure to __upload a file__ "
                        f"that only includes the code required for the challenge!"
                    )
                    return await message.channel.send(msg, delete_after=10.0)

                filetype = attach.filename.split(".")[-1]

                if len(filetype) > 4 or len(filetype) == 0:  # Most filetypes are 2-3 chars, 4 just to be safe
                    return await message.channel.send(
                        f"{message.author.mention} attachment file extension must be between 1 and 4 characters long",
                        delete_after=10.0,
                    )

                code = (await attach.read()).decode("u8")

                content = f"```{filetype}\n" + code.replace("`", "\u200b`") + "```"
                if len(content) > 4096:
                    # 4096 = max embed description size

                    msg = (
                        f"{message.author.mention} your submission can't be __more"
                        f" than {4096 - len(filetype) - 7} characters__."
                    )
                    return await message.channel.send(msg, delete_after=10.0)

                await message.author.add_roles(submitted)
                embed = discord.Embed(description=content, color=0x36393E)
                embed.set_author(name=str(message.author), icon_url=message.author.avatar.url)
                embed.set_footer(text=f"#ID: {message.author.id} • {len(code)} chars • Language: {filetype}")
                await submission_channel.send(embed=embed)

        elif message.channel.id in (TIMATHON_CHANNEL_ID, CHALLENGE_POST_CHANNEL_ID):  # Automatic reaction
            await message.add_reaction("🖐️")
