from discord.ext import commands
import discord
from config import STAFF_ROLE_ID, SUBMITTED_ROLE_ID, CHALLENGE_HOST_HELPER_ROLE_ID

def setup(bot):
    bot.add_cog(ChallengeHandler(bot))


class ChallengeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="challenges", aliases=("c",))
    async def challenges_group(self, ctx: commands.Context) -> None:
        """All of the Challenges commands"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)
    
    @challenges_group.command(
        name="resubmit",
        aliases=("rs",),
        brief="Resubmit Command to remove submitted role"
    )
    @commands.has_any_role(STAFF_ROLE_ID, CHALLENGE_HOST_HELPER_ROLE_ID) # Staff role or challenge host helper
    async def challenges_resubmit(self, ctx: commands.Context, member: discord.Member):
        
        submitted_role = ctx.guild.get_role(SUBMITTED_ROLE_ID)  # Submitted role

        if submitted_role in member.roles:  # Checking is user has the submitted role
            await member.remove_roles(submitted_role)
            return await ctx.send(f"Submitted role removed from {member.mention}")
    
        return await ctx.send(f"Member doesn't have the submitted role")
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Participant role.
        if payload.emoji != discord.PartialEmoji(name="🖐️"):
            return

        if payload.channel_id == 680851798340272141:
            submitted = self.bot.guild.get_role(687417501931536478)
            if submitted in payload.member.roles:
                return

            participant = self.bot.guild.get_role(687417513918857232)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

        elif payload.channel_id == 713841395965624490:
            submitted = self.bot.guild.get_role(715676464573317220)
            if submitted in payload.member.roles:
                return

            participant = self.bot.guild.get_role(715676023387062363)
            await self.bot.guild.get_member(payload.user_id).add_roles(participant)

    @commands.Cog.listener()
    async def on_message(self, message):  # Submitted role.

        if message.channel.id in (680851820587122700, 713841306253656064):  # weekly

            if message.author.id == self.bot.user.id:
                return

            if message.author.bot:
                return await message.delete()

            if message.channel.id == 680851820587122700:  # weekly 1
                submitted = self.bot.guild.get_role(687417501931536478)
                submission_channel = self.bot.guild.get_channel(729453161885990924)

            else:  # weekly 2
                submitted = self.bot.guild.get_role(715676464573317220)
                submission_channel = self.bot.guild.get_channel(729453201081761862)

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
                        f"{message.author.mention} attachement file extension must be between 1 and 4 characters long",
                        delete_after=10.0,
                    )

                code = (await attach.read()).decode("u8")

                content = (
                    f"```{filetype}\n"
                    + code.replace("`", "\u200b`")
                    + "```"
                )
                if len(content) > 4096:
                    # 4096 = max embed description size

                    msg = (
                        f"{message.author.mention} your submission can't be __more"
                        f" than {4096 - len(filetype) - 7} characters__."
                    )
                    return await message.channel.send(msg, delete_after=10.0)

                await message.author.add_roles(submitted)
                embed = discord.Embed(description=content, color=0x36393E)
                embed.set_author(
                    name=str(message.author), icon_url=message.author.avatar_url
                )
                embed.set_footer(
                    text=f"#ID: {message.author.id} • {len(code)} chars • Language: {filetype}"
                )
                await submission_channel.send(embed=embed)

        elif message.channel.id in [
            680851798340272141,
            713841395965624490,
        ]:  # Automatic reaction
            await message.add_reaction("🖐️")
