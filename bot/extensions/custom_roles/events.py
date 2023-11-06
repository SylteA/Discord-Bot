import datetime

import discord
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.models.custom_roles import CustomRole


class CustomRoleEvents(commands.Cog):
    """Events for Levelling in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.updated_at: dict[int, datetime] = {}

    @property
    def custom_roles_logs_channel(self) -> discord.TextChannel | None:
        return self.bot.guild.get_channel(settings.custom_roles.log_channel_id)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        try:
            if datetime.datetime.now() - self.updated_at[before.id] < datetime.timedelta(0, 10):
                query = """UPDATE custom_roles
                              SET name = $2, color = $3
                            WHERE role_id = $1
                        RETURNING *"""
                await CustomRole.fetchrow(query, before.id, after.name, after.color)

        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_custom_role_create(self, data: CustomRole):
        """Logs the creation of new role"""
        embed = discord.Embed(
            description=f"### <@{data.user_id}> Custom Role Created",
            color=discord.Color.brand_green(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="Name", value=data.name)
        embed.add_field(name="Color", value=str(data.color))
        embed.set_thumbnail(url=(await self.bot.fetch_user(data.user_id)).avatar)

        self.updated_at.setdefault(data.role_id, datetime.datetime.now())

        return await self.custom_roles_logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_custom_role_update(self, before: CustomRole, after: CustomRole):
        """Logs the update of custom role."""
        embed = discord.Embed(
            description=f"### <@{before.user_id}> Custom Role Updated",
            color=discord.Color.brand_green(),
            timestamp=datetime.datetime.utcnow(),
        )

        embed.add_field(name="Old Name", value=before.name)
        embed.add_field(name="New Name", value=after.name)
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Old Color", value=before.color)
        embed.add_field(name="New Color", value=str(after.color))
        embed.add_field(name="\u200B", value="\u200B")
        embed.set_thumbnail(url=(await self.bot.fetch_user(before.user_id)).avatar)

        self.updated_at.setdefault(after.role_id, datetime.datetime.now())

        return await self.custom_roles_logs_channel.send(embed=embed)
