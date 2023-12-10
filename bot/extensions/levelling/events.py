from discord.ext import commands

from bot import core
from bot.models import LevellingRole, LevellingUser


class LevellingEvents(commands.Cog):
    """Events for Levelling in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_xp_update(self, after: LevellingUser):
        if after.total_xp == after.total_xp - after.random_xp:
            return

        elif after.total_xp > after.total_xp - after.random_xp:
            query = """
                SELECT COALESCE(array_agg(role_id), '{}')
                  FROM levelling_roles lr
                 WHERE lr.guild_id = $1
                   AND lr.required_xp <= $2
                   AND lr.role_id NOT IN (
                    SELECT pr.role_id
                      FROM persisted_roles pr
                     WHERE pr.guild_id = lr.guild_id
                       AND pr.user_id = $3
                   )
            """
            # Fetch role ids that the user qualifies for, but have not been persisted.
            role_ids = await LevellingRole.fetchval(query, after.guild_id, after.total_xp, after.user_id)

            if not role_ids:
                return

            self.bot.dispatch("persist_roles", guild_id=after.guild_id, user_id=after.user_id, role_ids=role_ids)

        else:
            query = """
                SELECT COALESCE(array_agg(role_id), '{}')
                  FROM levelling_roles lr
                 WHERE lr.guild_id = $1
                   AND lr.required_xp > $2
                   AND lr.role_id IN (
                    SELECT pr.role_id
                      FROM persisted_roles pr
                     WHERE pr.guild_id = lr.guild_id
                       AND pr.user_id = $3
                   )
            """

            role_ids = await LevellingRole.fetchval(query, after.guild_id, after.total_xp, after.user_id)

            if not role_ids:
                return

            self.bot.dispatch(
                "remove_persisted_roles", guild_id=after.guild_id, user_id=after.user_id, role_ids=role_ids
            )
