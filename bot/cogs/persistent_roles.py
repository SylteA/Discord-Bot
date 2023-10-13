from discord.ext import commands

from bot.models import PersistentRole


class PersistentRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Get the data
        data = await PersistentRole.list_by_guild(member.guild.id, member.id)
        # Return if data for specified user and guild does not exist
        if data is None:
            return
        # Add the roles to the user if data exists
        else:
            for i in range(len(data)):
                await member.add_roles(member.guild.get_role(data[i].role_id))


async def setup(bot: commands.Bot):
    await bot.add_cog(PersistentRoles(bot=bot))
