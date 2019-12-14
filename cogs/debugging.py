from jishaku.metacog import GroupCogMeta
from jishaku.cog import jsk
from jishaku import JishakuBase


class Jsk(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk, command_attrs=dict(hidden=True)):
    async def cog_check(self, ctx):
        """Not everyone needs access to this"""
        if ctx.author.id not in (144112966176997376, 501089409379205161):
            return False
        return True


def setup(bot):
    bot.add_cog(Jsk(bot))
