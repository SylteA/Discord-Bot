from discord.ext import commands
import discord


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

        if message.channel.id in (680851820587122700, 713841306253656064):  # weekly
            if message.author.bot and message.author.id != self.bot.user.id:
                return await message.delete()
            
            if message.channel.id == 680851820587122700:  # weekly 1 
                submitted = self.bot.guild.get_role(687417501931536478)
                participant = self.bot.guild.get_role(687417513918857232)
                submission_channel = self.bot.guild.get_channel(729453161885990924)
            else:  # weekly 2
                submitted = self.bot.guild.get_role(715676464573317220)
                participant = self.bot.guild.get_role(715676023387062363)
                submission_channel = self.bot.guild.get_channel(729453201081761862)

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

        elif message.channel.id in [680851798340272141, 713841395965624490]:  # Automatic reaction
            await message.add_reaction("🖐️")
