import asyncio
import logging
import random
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from bot import core
from bot.extensions.levelling import utils
from bot.models import IgnoredChannel, LevellingRole, LevellingUser
from bot.models.custom_roles import CustomRole
from cli import ROOT_DIR

log = logging.getLogger(__name__)


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

        # Initializing fonts
        font = f"{ROOT_DIR.as_posix()}/assets/ABeeZee-Regular.otf"
        self.big_font = ImageFont.truetype(font, 60)
        self.medium_font = ImageFont.truetype(font, 40)
        self.small_font = ImageFont.truetype(font, 30)

        # Initialize the default background image for rank card
        self.background = Image.open(f"{ROOT_DIR.as_posix()}/assets/background.png")

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

    def generate_rank_image(self, username: str, avatar_bytes: bytes, rank: int, level: int, xp: int, required_xp: int):
        img = Image.new("RGBA", (1000, 240))
        logo = Image.open(BytesIO(avatar_bytes)).resize((200, 200))

        # Paste the default background image onto the new image
        img.paste(self.background, (0, 0))

        # Create a translucent dark layer to see the text better
        dark_layer = Image.new("RGBA", img.size, (0, 0, 0, 128))
        img = Image.alpha_composite(img, dark_layer)

        bigsize = (logo.size[0] * 3, logo.size[1] * 3)
        mask = Image.new("L", bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, bigsize[0], bigsize[1]), fill=255)
        mask = mask.resize(logo.size, Image.Resampling.LANCZOS)
        logo.putalpha(mask)

        img.paste(logo, (20, 20), mask=logo)

        draw = ImageDraw.Draw(img, "RGBA")

        # Placing Level text (right-upper part)
        text_size = draw.textbbox((0, 0), f"{level}", font=self.big_font)
        offset_x = 1000 - 43 - text_size[2]
        offset_y = 5
        draw.text((offset_x, offset_y), f"{level}", font=self.big_font, fill="#11ebf2")
        text_size = draw.textbbox((0, 0), "LEVEL", font=self.small_font)

        offset_x -= 5 + (text_size[2] - text_size[0])
        offset_y = 35
        draw.text((offset_x, offset_y), "LEVEL", font=self.small_font, fill="#11ebf2")

        # Placing Rank Text (right-upper part)
        text_size = draw.textbbox((0, 0), f"#{rank}", font=self.big_font)
        offset_x -= 15 + (text_size[2] - text_size[0])
        offset_y = 8
        draw.text((offset_x, offset_y), f"#{rank}", font=self.big_font, fill="#fff")

        text_size = draw.textbbox((0, 0), "RANK", font=self.small_font)
        offset_x -= 5 + (text_size[2] - text_size[0])
        offset_y = 35
        draw.text((offset_x, offset_y), "RANK", font=self.small_font, fill="#fff")

        # Placing Progress Bar
        bar_offset_x = logo.size[0] + 20 + 100
        bar_offset_y = 160
        bar_offset_x_1 = 1000 - 50
        bar_offset_y_1 = 200
        circle_size = bar_offset_y_1 - bar_offset_y

        # Progress bar rect greyer one
        draw.rectangle((bar_offset_x, bar_offset_y, bar_offset_x_1, bar_offset_y_1), fill="#727175")

        # Left circle
        draw.ellipse(
            (
                bar_offset_x - circle_size // 2,
                bar_offset_y,
                bar_offset_x + circle_size // 2,
                bar_offset_y + circle_size,
            ),
            fill="#727175",
        )

        # Right Circle
        draw.ellipse(
            (bar_offset_x_1 - circle_size // 2, bar_offset_y, bar_offset_x_1 + circle_size // 2, bar_offset_y_1),
            fill="#727175",
        )

        # Filling Progress Bar
        bar_length = bar_offset_x_1 - bar_offset_x

        progress = (required_xp - xp) * 100 / required_xp
        progress = 100 - progress
        progress_bar_length = round(bar_length * progress / 100)
        pbar_offset_x_1 = bar_offset_x + progress_bar_length

        # Drawing Rectangle
        draw.rectangle((bar_offset_x, bar_offset_y, pbar_offset_x_1, bar_offset_y_1), fill="#11ebf2")

        # Left circle
        draw.ellipse(
            (
                bar_offset_x - circle_size // 2,
                bar_offset_y,
                bar_offset_x + circle_size // 2,
                bar_offset_y + circle_size,
            ),
            fill="#11ebf2",
        )

        # Right Circle
        draw.ellipse(
            (pbar_offset_x_1 - circle_size // 2, bar_offset_y, pbar_offset_x_1 + circle_size // 2, bar_offset_y_1),
            fill="#11ebf2",
        )

        def convert_int(integer):
            if integer >= 1000:
                integer = round(integer / 1000, 2)
                return f"{integer}K"
            else:
                return str(integer)

        # Drawing Xp Text
        text = f"/ {convert_int(required_xp)} XP"
        xp_text_size = draw.textbbox((0, 0), text, font=self.small_font)
        xp_offset_x = bar_offset_x_1 - (xp_text_size[2] - xp_text_size[0])
        xp_offset_y = bar_offset_y - xp_text_size[3] - 10
        draw.text((xp_offset_x, xp_offset_y), text, font=self.small_font, fill="#727175")

        text = f"{convert_int(xp)} "
        xp_text_size = draw.textbbox((0, 0), text, font=self.small_font)
        xp_offset_x -= xp_text_size[2] - xp_text_size[0]
        draw.text((xp_offset_x, xp_offset_y), text, font=self.small_font, fill="#fff")

        if len(username) >= 18:
            # Truncating the name
            username = username[:15] + "..."

        text_bbox = draw.textbbox((0, 0), username, font=self.medium_font)
        text_offset_y = bar_offset_y - (text_bbox[3] - text_bbox[1]) - 20
        draw.text((bar_offset_x, text_offset_y), username, font=self.medium_font, fill="#fff")

        # create copy of background
        background = self.background.copy()

        # Paste the content image into the center of the background
        bg_width, bg_height = background.size
        img_width, img_height = img.size
        x = (bg_width - img_width) // 2
        y = (bg_height - img_height) // 2
        background.paste(img, (x, y))

        buf = BytesIO()
        background.save(buf, "PNG")
        buf.seek(0)
        return buf

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

        if record.total_xp is None:
            if member.id == interaction.user.id:
                return await interaction.response.send_message(
                    "You are not ranked yet, send a few messages and try again!", ephemeral=True
                )

            return await interaction.response.send_message("That user is not ranked yet...", ephemeral=True)

        # Fetch the user's avatar as bytes
        avatar_bytes = await member.avatar.with_format("png").read()

        level = utils.get_level_for_xp(record.total_xp)
        prev_xp = utils.get_xp_for_level(level)
        next_xp = utils.get_xp_for_level(level + 1) - prev_xp
        curr_xp = record.total_xp - prev_xp

        # Run the image generation in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self.generate_rank_image, member.display_name, avatar_bytes, record.count + 1, level, curr_xp, next_xp
        )

        # Send result as image
        await interaction.response.send_message(
            file=discord.File(result, filename="rank.png"),
            allowed_mentions=discord.AllowedMentions.none(),
        )

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
