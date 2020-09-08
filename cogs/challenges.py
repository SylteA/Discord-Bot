from discord.ext import commands
import discord
import re

GITHUB_REGEX = re.compile(r"(https://github.com/[a-zA-Z0-9]+/[a-zA-Z0-9]+)")


def setup(bot):
    bot.add_cog(ChallengeHandler(bot))


class ChallengeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        if message.channel.id == 680851820587122700:  # weekly
            if message.author.bot:
                return await message.delete()
            
            submitted = self.bot.guild.get_role(687417501931536478)
            participant = self.bot.guild.get_role(687417513918857232)
            submission_channel = self.bot.guild.get_channel(729453161885990924)
            discussion_channel = self.bot.guild.get_channel(680851838857117770)

            if submitted not in message.author.roles:
                await message.delete()
                if message.content.count("```") != 2:
                    msg = f"{message.author.mention} make sure to submit in a code " \
                          f"block and only include the code required for the challenge!" \
                          f"\nUse `tim.tag discord code` for more information!"
                    return await message.channel.send(msg, delete_after=10.0)

                await message.author.add_roles(submitted)
                await message.author.remove_roles(participant)
                embed = discord.Embed(description=message.content,
                                      color=message.guild.me.top_role.color)
                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
                embed.set_footer(text=f'#ID: {message.author.id}')
                await submission_channel.send(embed=embed)

        elif message.channel.id == 713841306253656064:  # monthly 
            if message.author.bot:
                return await message.delete()
            
            submitted = self.bot.guild.get_role(715676464573317220)
            participant = self.bot.guild.get_role(715676023387062363)
            submission_channel = self.bot.guild.get_channel(729453201081761862)

            await message.delete()

            links = GITHUB_REGEX.findall(message.content)
            if not links:
                return await message.author.send(f'{message.author.mention} Could not find any valid "Github" url.')

            if len(links) > 1:
                return await message.author.send(f'{message.author.mention} Please only provide one "Github" url.')

            if len(message.mentions) == 0:
                return await message.author.send(f"{message.author.mention}, Please make sure to mention your team ("
                                                 f"yourself included)")

            for member in message.mentions:
                if participant not in member.roles:
                    return await message.author.send(f"{member.mention} didn't participated in the challenge")
                if submitted in member.roles:
                    return await message.author.send(f"{member.mention} has already submitted")

            for member in message.mentions:
                await member.add_roles(submitted)
                await member.remove_roles(participant)

            embed = discord.Embed(description=message.content,
                                  color=message.guild.me.top_role.color)
            embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
            embed.set_footer(text=f'#ID: {message.author.id}')
            await submission_channel.send(embed=embed)

        elif message.channel.id in [680851798340272141, 713841395965624490]:  # Automatic reaction
            await message.add_reaction("🖐️")
