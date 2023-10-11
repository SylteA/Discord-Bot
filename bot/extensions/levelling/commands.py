import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions

from bot import core
from bot.models import IgnoredChannel, Levels

REQUIRED_XP = [
    0,
    100,
    255,
    475,
    770,
    1150,
    1625,
    2205,
    2900,
    3720,
    4675,
    5775,
    7030,
    8450,
    10045,
    11825,
    13800,
    15980,
    18375,
    20995,
    23850,
    26950,
    30305,
    33925,
    37820,
    42000,
    46475,
    51255,
    56350,
    61770,
    67525,
    73625,
    80080,
    86900,
    94095,
    101675,
    109650,
    118030,
    126825,
    136045,
    145700,
    155800,
    166355,
    177375,
    188870,
    200850,
    213325,
    226305,
    239800,
    253820,
    268375,
    283475,
    299130,
    315350,
    332145,
    349525,
    367500,
    386080,
    405275,
    425095,
    445550,
    466650,
    488405,
    510825,
    533920,
    557700,
    582175,
    607355,
    633250,
    659870,
    687225,
    715325,
    744180,
    773800,
    804195,
    835375,
    867350,
    900130,
    933725,
    968145,
    1003400,
    1039500,
    1076455,
    1114275,
    1152970,
    1192550,
    1233025,
    1274405,
    1316700,
    1359920,
    1404075,
    1449175,
    1495230,
    1542250,
    1590245,
    1639225,
    1689200,
    1740180,
    1899250,
    1792175,
    1845195,
]


class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignored_channel = {}

    async def cog_load(self):
        for guild in self.bot.guilds:
            data = await IgnoredChannel.get(guild_id=guild.id)
            for i in data:
                if guild.id not in self.ignored_channel:
                    self.ignored_channel[guild.id] = [i.channel_id]
                else:
                    self.ignored_channel[guild.id].append(i.channel_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Return if message was sent by Bot or sent in DMs
        if message.author.bot or message.guild is None:
            return

        # Check if message is sent in ignored channel
        if message.channel.id in self.ignored_channel[message.guild.id]:
            return

        # Generate random XP to be added
        xp = random.randint(5, 25)
        # Add the XP and update the DB
        data = await Levels.update(guild_id=message.guild.id, user_id=message.author.id, total_xp=xp)
        await self._check_level_up(data, message.author)

    @app_commands.command()
    async def rank(self, interaction: core.InteractionType, member: discord.Member = None):
        """Check the rank of another member or yourself"""
        if member is None:
            member = interaction.user

        query = """WITH ordered_users AS (
                        SELECT
                        user_id,guild_id,total_xp,
                        ROW_NUMBER() OVER (ORDER BY levels.total_xp DESC) AS rank
                        FROM levels
                        WHERE guild_id = $2)
                        SELECT rank,total_xp,user_id,guild_id
                        FROM ordered_users WHERE ordered_users.user_id = $1;"""
        data = await Levels.fetchrow(query, member.id, member.guild.id)
        if data is None:
            return await interaction.response.send_message("You are not ranked yet!", ephemeral=True)
        for level, j in enumerate(REQUIRED_XP):
            if data.total_xp <= j:
                embed = discord.Embed(
                    title=f"Rank: {data.rank}\nLevel: {level - 1}\nTotal XP:{data.total_xp}",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.blurple(),
                )
                embed.set_thumbnail(url=member.avatar)
                return await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def ignore_channel(self, interaction: core.InteractionType, channel: discord.TextChannel):
        """Add the channel to the ignored channel list to not gain XP"""
        await IgnoredChannel.insert(channel.guild.id, channel.id)
        await interaction.response.send_message(f"{channel} has been ignored from gaining XP.")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    @has_permissions(administrator=True)
    async def unignore_channel(self, interaction: core.InteractionType, channel: discord.TextChannel):
        """Remove channel from ignored channel list"""
        await IgnoredChannel.delete(channel.guild.id, channel.id)
        await interaction.response.send_message(f"{channel} has been removed from ignored channel list")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def give_xp(self, interaction: core.InteractionType, xp: int, member: discord.Member):
        """Give XP to specific user"""
        data = await Levels.update(member.guild.id, member.id, xp)
        await self._check_level_up(data, member)
        await interaction.response.send_message(f"{xp} XP has been added to user {member}")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_xp(self, interaction: core.InteractionType, xp: int, member: discord.Member):
        """Remove XP from user"""
        data = await Levels.remove_xp(member.guild.id, member.id, xp)
        await self._check_level_up(data, member)
        await interaction.response.send_message(f"{xp} XP has been removed from user {member}")

    async def _check_level_up(self, data, member: discord.Member):
        """Function to check if user's level has changed and trigger the event to assign the roles"""
        # Calculating old and new level
        try:
            for level, j in enumerate(REQUIRED_XP):
                if data.old_total_xp <= j:
                    old_level = level - 1
                    break
            for level, j in enumerate(REQUIRED_XP):
                if data.total_xp <= j:
                    new_level = level - 1
                    break
            # If the level has changed call level_up to handle roles change
            if old_level != new_level:
                self.bot.dispatch("level_up", new_level=new_level, member=member)
        except AttributeError:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Levelling(bot=bot))
