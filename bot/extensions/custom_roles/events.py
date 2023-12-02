import datetime
import time

import discord
from discord.ext import commands

from bot import core
from bot.models import Config, CustomRole


class CustomRoleEvents(commands.Cog):
    """Events for Levelling in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.updated_at: dict[int, datetime] = {}

    async def get_custom_roles_logs_channel(self):
        query = """SELECT * FROM configs
                    WHERE guild_id = $1"""
        data = await Config.fetchrow(query, self.bot.guild.id)
        return self.bot.guild.get_channel(data.custom_role_log_channel_id)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        last_update = self.updated_at.get(before.id)

        # Ignore events less than 10 seconds since a user updated their role
        if last_update is not None:
            if time.time() - last_update < 10:
                return

        query = """
            UPDATE custom_roles
               SET name = $2, color = $3
             WHERE role_id = $1
        """
        await CustomRole.execute(query, after.id, after.name, after.color.value)

    @commands.Cog.listener()
    async def on_custom_role_create(self, custom_role: CustomRole):
        """Logs the creation of new role"""
        self.updated_at[custom_role.role_id] = time.time()

        user = await self.bot.fetch_user(custom_role.user_id)

        embed = discord.Embed(
            title="Custom Role Created",
            color=discord.Color.brand_green(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)
        embed.add_field(name="Name", value=custom_role.name)
        embed.add_field(name="Color", value="#" + hex(custom_role.color)[2:])
        embed.set_thumbnail(url=user.avatar)
        embed.set_footer(text=f"user_id: {custom_role.user_id}")

        channel = await self.get_custom_roles_logs_channel()
        return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_custom_role_update(self, before: CustomRole, after: CustomRole):
        """Logs the update of custom role."""
        self.updated_at[after.role_id] = time.time()

        user = await self.bot.fetch_user(after.user_id)

        embed = discord.Embed(
            title="Custom Role Updated",
            color=discord.Color.brand_green(),
            timestamp=datetime.datetime.utcnow(),
        )

        if before.name == after.name:
            embed.add_field(name="Name", value=before.name)
        else:
            embed.add_field(name="Name (Updated)", value=f"{before.name} -> {after.name}")

        embed.add_field(name="\u200B", value="\u200B")

        if before.color == after.color:
            embed.add_field(name="Color", value="#" + hex(after.color)[2:])
        else:
            embed.add_field(name="Color (Updated)", value=f"#{hex(before.color)[2:]} -> #{hex(after.color)[2:]}")

        embed.set_thumbnail(url=user.avatar)
        embed.set_author(name=user.name, icon_url=user.avatar)
        embed.set_footer(text=f"user_id: {after.user_id}")

        channel = await self.get_custom_roles_logs_channel()
        return await channel.send(embed=embed)
