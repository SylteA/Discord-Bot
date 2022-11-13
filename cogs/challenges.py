import discord
from discord.ext import commands

from config import settings


def check(ctx):
    roles = [r.id for r in ctx.author.roles]
    return 713170076148433017 in roles or 767389648048619553 in roles


class ChallengeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_any_role(
        settings.moderation.staff_role_id, settings.challenges.host_role_id, settings.challenges.host_helper_role_id
    )
    @commands.group(name="challenges", aliases=("c",))
    async def challenges_group(self, ctx: commands.Context) -> None:
        """All of the Challenges commands"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @challenges_group.command(
        name="remove_winners",
        aliases=("rwr"),
        brief="Remove Challenge Winner roles"
    )
    @commands.check(check)
    async def remove_winners(ctx):
        role = ctx.guild.get_role(692022273934360586)
        for member in role.members:
            await member.remove_roles(role)
        await ctx.send("Done.")

    @challenges_group.command(
        name="assign_winners", 
        aliases=("awr"),
        brief="Assign Challenge Winner roles")
    @commands.check(check)
    async def assign_winners(ctx, message: discord.Message):
        m = await bot.get_channel(680851838857117770).fetch_message(message.id)
        for i in re!.findall(r"<@!?(\d+)>", m.embeds[0].description):
            member = guild.get_member(int(i))
            if member:
                await member.add_roles(discord.Object(id=692022273934360586))
            else:
                await ctx.send(str(await bot.fetch_user(int(i))))
        await ctx.send("Done.")

    @challenges_group.command(
        name="resubmit",
        aliases=("rs",),
        brief="Resubmit Command to remove submitted role",
    )
    async def challenges_resubmit(self, ctx: commands.Context, member: discord.Member):
        submitted_role = ctx.guild.get_role(settings.challenges.submitted_role_id)

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
        info_channel = ctx.guild.get_channel(settings.challenges.info_channel_id)

        return await info_channel.send(
            f"<@&{settings.challenges.winner_role_id}> :pancakes: have been given out, "
            f"go deposit them in <#{settings.bot.games_channel_id}>. \n"
            f"Analysis for the challenge will be available shortly in <#{settings.challenges.info_channel_id}>",
            allowed_mentions=discord.AllowedMentions(roles=[discord.Object(settings.challenges.winner_role_id)]),
        )

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @challenges_group.command(
        name="open_submissions",
        aliases=("os", "open"),
        brief="Command to open submissions",
    )
    async def open_submissions(self, ctx: commands.Context):
        info_channel = ctx.guild.get_channel(settings.challenges.info_channel_id)

        submit_channel = ctx.guild.get_channel(settings.challenges.submit_channel_id)

        # Allows people to submit
        overwrite = submit_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await submit_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        return await info_channel.send(
            f"<@&{settings.challenges.participant_role_id}> Submissions are open."
            f"Upload your code file with extension in <#{settings.challenges.submit_channel_id}>. "
            f"Send `t.tag submitting` in <#{settings.bot.commands_channels_ids[0]}> for more details",
            allowed_mentions=discord.AllowedMentions(roles=[discord.Object(settings.challenges.participant_role_id)]),
        )

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @challenges_group.command(
        name="close_submissions",
        aliases=("cs", "close"),
        brief="Command to close submissions",
    )
    async def close_submissions(self, ctx: commands.Context):
        info_channel = ctx.guild.get_channel(settings.challenges.info_channel_id)

        submit_channel = ctx.guild.get_channel(settings.challenges.submit_channel_id)

        # Disallows people to submit
        overwrite = submit_channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await submit_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        return await info_channel.send(
            f"<@&{settings.challenges.submitted_role_id}> Submissions are closed. "
            "Testing will begin soon. See you in the next challenge",
            allowed_mentions=discord.AllowedMentions(roles=[discord.Object(settings.challenges.submitted_role_id)]),
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Participant role.
        if payload.emoji != discord.PartialEmoji(name="🖐️"):
            return

        if payload.channel_id == settings.challenges.channel_id:
            submitted = self.bot.guild.get_role(settings.challenges.submitted_role_id)
            if submitted in payload.member.roles:
                return

            participant = self.bot.guild.get_role(settings.challenges.participant_role_id)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

        elif payload.channel_id == settings.timathon.channel_id:

            participant = self.bot.guild.get_role(settings.timathon.participant_role_id)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

    @commands.Cog.listener()
    async def on_message(self, message):  # Submitted role.

        if message.channel.id == settings.challenges.submit_channel_id:

            if message.author.id == self.bot.user.id:
                return

            if message.author.bot:
                return await message.delete()

            submitted = self.bot.guild.get_role(settings.challenges.submitted_role_id)
            hidden_submission_channel = self.bot.guild.get_channel(settings.challenges.submissions_channel_id)

            if submitted not in message.author.roles:
                await message.delete()
                attach = message.attachments and message.attachments[0]

                if not attach:
                    msg = (
                        f"{message.author.mention} make sure to __upload a "
                        f"file__ that only includes the code required "
                        f"for the challenge!"
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
                await hidden_submission_channel.send(embed=embed)

        elif message.channel.id in [
            settings.challenges.channel_id,
            settings.timathon.channel_id,
        ]:  # Automatic reaction
            await message.add_reaction("🖐️")


async def setup(bot):
    await bot.add_cog(ChallengeHandler(bot))
