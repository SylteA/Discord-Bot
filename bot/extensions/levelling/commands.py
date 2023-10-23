import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.extensions.levelling import utils
from bot.models import IgnoredChannel, LevellingRole, LevellingUser
from bot.models.custom_roles import CustomRole


class Levelling(commands.Cog):
    admin_commands = app_commands.Group(
        name="levelling",
        description="Levelling commands for staff",
        default_permissions=discord.Permissions(administrator=True),
    )

    ignored_channels = app_commands.Group(
        parent=admin_commands,
        name="ignored_channels",
        description="Commands to manage XP ignored channels.",
        default_permissions=discord.Permissions(administrator=True),
    )

    xp = app_commands.Group(
        parent=admin_commands,
        name="experience",
        description="Manually update the XP of a player.",
        default_permissions=discord.Permissions(administrator=True),
    )

    rewards = app_commands.Group(
        parent=admin_commands,
        name="rewards",
        description="Manage the roles given at a certain amount of xp.",
        default_permissions=discord.Permissions(administrator=True),
    )

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        self.ignored_channels: dict[int, list[int]] = {}
        self.required_xp = [0]
        self.xp_boost = 1

    async def cog_load(self):
        query = """
            SELECT *
              FROM levelling_ignored_channels
             WHERE guild_id = ANY($1)
        """
        guild_ids = [guild.id for guild in self.bot.guilds]
        self.ignored_channels = {guild.id: [] for guild in self.bot.guilds}

        channels = await IgnoredChannel.fetch(query, guild_ids)

        for channel in channels:
            self.ignored_channels[channel.guild_id].append(channel.channel_id)

        for lvl in range(101):
            xp = 5 * (lvl**2) + (50 * lvl) + 100
            self.required_xp.append(xp + self.required_xp[-1])

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        if message.guild.id in self.ignored_channels:
            if message.channel.id in self.ignored_channels[message.guild.id]:
                return

        query = """
            INSERT INTO levelling_users (guild_id, user_id, total_xp)
                 VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, user_id)
              DO UPDATE SET
               total_xp = levelling_users.total_xp + $3,
               last_msg = create_snowflake()
                  WHERE levelling_users.guild_id = $1
                    AND levelling_users.user_id = $2
                    AND snowflake_to_timestamp(levelling_users.last_msg) < NOW() - INTERVAL '1 min'
              RETURNING *;
        """

        # TODO: Allow each guild to set custom xp range and boost.
        xp = random.randint(5, 25) * self.xp_boost
        after = await LevellingUser.fetchrow(query, message.guild.id, message.author.id, xp)

        if after is None:
            return  # Last message was less than a minute ago.

        before = after.copy(update={"total_xp": after.total_xp - xp})

        self.bot.dispatch("xp_update", before=before, after=after)

    @app_commands.command()
    async def rank(self, interaction: core.InteractionType, member: discord.Member = None):
        """Check the rank of another member or yourself"""
        member = member or interaction.user

        query = """
            WITH "user" AS (
                SELECT total_xp
                  FROM levelling_users
                 WHERE guild_id = $1
                   AND user_id = $2
            )
            SELECT (SELECT total_xp FROM "user"), COUNT(*)
              FROM levelling_users
             WHERE guild_id = $1
               AND total_xp > (SELECT total_xp FROM "user");
        """

        record = await LevellingUser.pool.fetchrow(query, interaction.guild.id, member.id)

        if record is None:
            return await interaction.response.send_message("User Not ranked yet!", ephemeral=True)

        level = utils.get_level_for_xp(user_xp=record.total_xp)

        embed = discord.Embed(
            title=f"Rank: {record.count + 1}\nLevel: {level}, Total XP: {record.total_xp}",
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.avatar)
        return await interaction.response.send_message(embed=embed)

    @ignored_channels.command()
    @app_commands.describe(channel="The channel to ignore.")
    async def add(self, interaction: core.InteractionType, channel: discord.TextChannel):
        """Add a channel to the list of ignored channels."""
        if channel.guild.id not in self.ignored_channels:
            self.ignored_channels[channel.guild.id] = []

        if channel.id in self.ignored_channels[channel.guild.id]:
            return await interaction.response.send_message("That channel is already ignored.", ephemeral=True)

        self.ignored_channels[channel.guild.id].append(channel.id)

        query = """
            INSERT INTO levelling_ignored_channels (guild_id, channel_id)
                 VALUES ($1, $2)
            ON CONFLICT (guild_id, channel_id) DO NOTHING
        """
        await IgnoredChannel.execute(query, channel.guild.id, channel.id)
        return await interaction.response.send_message(f"I'll now ignore messages in {channel.mention}.")

    @ignored_channels.command()
    @app_commands.describe(channel="The channel to remove.")
    async def remove(self, interaction: core.InteractionType, channel: discord.TextChannel):
        """Remove a channel from the list of ignored channels."""
        if channel.id not in self.ignored_channels.get(channel.guild.id, []):
            return await interaction.response.send_message("That channel is not ignored", ephemeral=True)

        self.ignored_channels[channel.guild.id].remove(channel.id)

        query = """
            DELETE FROM levelling_ignored_channels
                  WHERE channel_id = $1
        """
        await IgnoredChannel.execute(query, channel.id)
        return await interaction.response.send_message(f"No longer ignoring messages in {channel.mention}.")

    @ignored_channels.command(name="list")
    @app_commands.describe(ephemeral="If true, only you can see the response.")
    async def list_channels(self, interaction: core.InteractionType, ephemeral: bool = True):
        """Lists the ignored channels in this guild."""
        ignored_channels = self.ignored_channels.get(interaction.guild.id, [])

        response = f"## Listing `{len(ignored_channels)}` ignored channels\n\n"

        for channel_id in ignored_channels:
            channel = interaction.guild.get_channel(channel_id)

            if channel is None:
                response += f"- Unknown Channel (`{channel_id}`)\n"
            else:
                response += f"- {channel.mention}\n"

        return await interaction.response.send_message(response, ephemeral=ephemeral)

    async def update_user_xp(self, guild_id: int, user_id: int, amount: int):
        query = """
            INSERT INTO levelling_users (guild_id, user_id, total_xp)
                 VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, user_id)
              DO UPDATE SET
               total_xp = GREATEST(levelling_users.total_xp + $3, 0),
               last_msg = create_snowflake()
                  WHERE levelling_users.guild_id = $1
                    AND levelling_users.user_id = $2
              RETURNING *;
        """

        after = await LevellingUser.fetchrow(query, guild_id, user_id, amount)
        before = after.copy(update={"total_xp": after.total_xp - amount})

        self.bot.dispatch("xp_update", before=before, after=after)

    @xp.command(name="add")
    @app_commands.describe(member="The member member to add xp to.", amount="The amount of xp to give.")
    async def add_xp(self, interaction: core.InteractionType, member: discord.Member, amount: int):
        """Give XP to the specified user"""
        if amount <= 0:
            return await interaction.response.send_message("Amount must be a positive integer.", ephemeral=True)

        if member.bot:
            return await interaction.response.send_message("Cannot add experience to a bot.", ephemeral=True)

        await self.update_user_xp(guild_id=member.guild.id, user_id=member.id, amount=amount)
        return await interaction.response.send_message(f"Added `{amount}` XP to {member.display_name}")

    @xp.command(name="remove")
    @app_commands.describe(member="The member member to add xp to.", amount="The amount of xp to give.")
    async def remove_xp(self, interaction: core.InteractionType, member: discord.Member, amount: int):
        """Remove XP from the specified user."""
        if amount <= 0:
            return await interaction.response.send_message("Amount must be a positive integer.", ephemeral=True)

        if member.bot:
            return await interaction.response.send_message("Cannot remove experience from a bot.", ephemeral=True)

        await self.update_user_xp(guild_id=member.guild.id, user_id=member.id, amount=-amount)
        return await interaction.response.send_message(f"Removed `{amount}` XP from {member.display_name}")

    @rewards.command(name="add")
    @app_commands.describe(role="The role to reward.", level="The level to reward it at.")
    async def add_role(self, interaction: core.InteractionType, role: discord.Role, level: int):
        """Add a levelling reward."""
        query = """
            INSERT INTO levelling_roles (guild_id, role_id, required_xp)
                 VALUES ($1, $2, $3)
            ON CONFLICT (guild_id, role_id)
                        DO NOTHING
              RETURNING *;
        """

        required_xp = utils.get_xp_for_level(level)

        await CustomRole.ensure_exists(
            guild_id=role.guild.id, role_id=role.id, name=role.name, color=str(role.color.value)
        )

        record = await LevellingRole.fetchrow(query, role.guild.id, role.id, required_xp)

        if record is None:
            return await interaction.response.send_message(
                f"{role.mention} is already a levelling reward.", ephemeral=True
            )

        return await interaction.response.send_message(
            f"{role.mention} has been added as a reward for reaching level {level}!",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @rewards.command(name="remove")
    async def remove_role(self, interaction: core.InteractionType, role: discord.Role):
        """Remove a levelling reward."""
        query = """
            DELETE FROM levelling_roles
                  WHERE role_id = $1
        """

        deleted = await LevellingRole.execute(query, role.id)
        # count = int(deleted.removeprefix("DELETE "))

        return await interaction.response.send_message(deleted, ephemeral=True)

    @rewards.command(name="list")
    async def list_roles(self, interaction: core.InteractionType):
        """Lists the levelling roles in this guild."""
        query = """
            SELECT *
              FROM levelling_roles
             WHERE guild_id = $1
        """

        rewards = await LevellingRole.fetch(query, interaction.guild.id)

        # TODO: This command needs to be fixed, the max role name length needs to be dynamic
        response = "| {:<10} | {:<5} |".format("Role Name", "Level")
        response += "\n|" + "-" * 12 + "|" + "-" * 7 + "|"

        for reward in rewards:
            role = interaction.guild.get_role(reward.role_id)
            level = utils.get_level_for_xp(reward.required_xp)

            role_name = f"Unknown role (`{reward.role_id}`)" if role is None else role.name

            response += "\n| {:<10} | {:<5} |".format(role_name, level)

        return await interaction.response.send_message(f"```\n{response}\n```\n")


async def setup(bot: core.DiscordBot):
    await bot.add_cog(Levelling(bot=bot))
