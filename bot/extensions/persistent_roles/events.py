import discord
from discord.ext import commands

from bot import core
from bot.models import PersistedRole


class PersistentEvents(commands.Cog):
    """Events for Persisted roles."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_remove_persisted_roles(self, guild_id: int, user_id: int, role_ids: list[int]):
        """This event is called to remove persisted roles from a user."""
        query = "DELETE FROM persisted_roles WHERE guild_id = $1 AND user_id = $2 AND role_id = ANY($3)"
        await PersistedRole.execute(query, guild_id, user_id, role_ids)

        guild = self.bot.get_guild(guild_id)

        if guild is None:
            return

        member = guild.get_member(user_id)

        if member is None:
            return

        roles = []

        for role_id in role_ids:
            role = member.get_role(role_id)

            if role is None:
                continue

            roles.append(role)

        await member.remove_roles(*roles, atomic=True)

    @commands.Cog.listener()
    async def on_persist_roles(self, guild_id: int, user_id: int, role_ids: list[int]):
        """This event is called to trigger persist of roles."""
        query = "INSERT INTO persisted_roles (guild_id, user_id, role_id) VALUES ($1, $2, $3)"
        data = [(guild_id, user_id, role_id) for role_id in role_ids]
        await PersistedRole.pool.executemany(query, data)

        guild = self.bot.get_guild(guild_id)

        if guild is None:
            return

        member = guild.get_member(user_id)

        if member is None:
            return

        roles = []

        for role_id in role_ids:
            role = guild.get_role(role_id)

            if role is None:
                continue

            roles.append(role)

        await member.add_roles(*roles, atomic=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Add the persisted role to users if any on member join"""
        query = """
            SELECT COALESCE(array_agg(role_id), '{}')
              FROM persisted_roles
             WHERE guild_id = $1
               AND user_id = $2
        """
        role_ids = await PersistedRole.fetchval(query, member.guild.id, member.id)

        roles = []

        for role_id in role_ids:
            role = member.guild.get_role(role_id)

            if role is None:
                continue

            roles.append(role)

        await member.add_roles(*roles)
