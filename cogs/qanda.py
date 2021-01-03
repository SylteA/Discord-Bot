from discord.ext import commands
import discord


def setup(bot):
    bot.add_cog(QandA(bot=bot))


class QandA(commands.Cog):
    """Temporary cog for Q&A command handling!"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message): -> None:
        if message.channel =! 795256498958630952:
            return
        
        role = discord.Object(id=795257055093981194)
        if role not in message.author.roles:
            await message.author.add_roles(role)
