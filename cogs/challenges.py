from discord.ext import commands


def setup(bot):
    bot.add_cog(ChallengeHandler(bot))


class ChallengeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):  # Participant role.

        if payload.channel_id != 680851798340272141:
            return

        submitted = self.bot.guild.get_role(687417501931536478)
        if submitted in payload.member.roles:
            return

        if str(payload.emoji) != "<:tick:582492227410984961>":
            return

        role = self.bot.guild.get_role(687417513918857232)
        await self.bot.guild.get_member(payload.user_id).add_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message):  # Submitted role.
        if message.channel.id != 680851820587122700:
            return

        submitted = self.bot.guild.get_role(687417501931536478)
        participant = self.bot.guild.get_role(687417513918857232)

        if submitted not in message.author.roles:
            await message.author.add_roles(submitted)
            await message.author.remove_roles(participant)
