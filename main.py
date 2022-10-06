#!/usr/bin/env python3
import asyncio
import datetime
import os

import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext.commands.errors import (
    BadArgument,
    BadUnionArgument,
    BotMissingAnyRole,
    BotMissingPermissions,
    BotMissingRole,
    CheckFailure,
    CommandOnCooldown,
    ConversionError,
    MissingAnyRole,
    MissingPermissions,
    MissingRequiredArgument,
    MissingRole,
    NoPrivateMessage,
    PrivateMessageOnly,
)

from cogs.utils.context import SyltesContext
from cogs.utils.DataBase import DataBase, Message, User
from cogs.utils.time import human_timedelta
from config import settings

os.environ.update(JISHAKU_NO_UNDERSCORE="True", JISHAKU_NO_DM_TRACEBACK="True", JISHAKU_HIDE="True")
initial_cogs = [
    "jishaku",
    "cogs.commands",
    "cogs.filtering",
    "cogs._help",
    "cogs.tags",
    "cogs.challenges",
    "cogs.clashofcode",
    "cogs.roles",
    "cogs.poll",
    "cogs.adventofcode",
]

print("Connecting...")


class Tim(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=kwargs.pop("command_prefix", ("t.", "T.", "tim.")),
            intents=discord.Intents.all(),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
            **kwargs,
        )
        self.session = ClientSession(loop=self.loop)
        self.start_time = datetime.datetime.utcnow()
        self.clean_text = commands.clean_content(escape_markdown=True, fix_channel_mentions=True)

    """  Events   """

    async def on_connect(self):
        """Connect DB before bot is ready to assure that no calls are made before its ready"""
        self.db = await DataBase.create_pool(bot=self, uri=settings.postgres.uri, loop=self.loop)

    async def on_ready(self):
        print(f"Successfully logged in as {self.user}\nSharded to {len(self.guilds)} guilds")
        self.guild = self.get_guild(settings.guild.id)
        self.welcomes = self.guild.get_channel(settings.guild.welcomes_channel_id)
        await self.change_presence(activity=discord.Game(name='use the prefix "tim."'))

        for ext in initial_cogs:
            self.load_extension(ext)
        print(f"Loaded all extensions after {human_timedelta(self.start_time, brief=True, suffix=False)}")

    async def on_member_join(self, member):
        await self.wait_until_ready()
        if member.guild.id == settings.guild.id:
            await self.welcomes.send(
                f"Welcome to the Tech With Tim Community {member.mention}!\n"
                f"Members += 1\nCurrent # of members: {self.guild.member_count}"
            )

    async def on_message(self, message):
        await self.wait_until_ready()

        if message.author.bot:
            return

        print(f"{message.channel}: {message.author}: {message.clean_content}")

        if not message.guild:
            return

        if message.channel.id == settings.challenges.submit_channel_id:
            return

        await self.process_commands(message)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message=message)

        if ctx.command is None:
            return await Message.on_message(bot=self, message=message)

        if ctx.command.name in (
            "help",
            "scoreboard",
            "rep_scoreboard",
            "reps",
            "member_count",
            "top_user",
            "users",
            "server_messages",
            "messages",
        ):
            if ctx.channel.id not in settings.bot.commands_channels_ids:
                return await message.channel.send(
                    f"**Please use the <#{settings.bot.commands_channels_ids[0]}> channel**"
                )

        try:
            await self.invoke(ctx)
        finally:
            await User.on_command(bot=self, user=message.author)

    async def on_command_error(self, ctx, exception):
        await self.wait_until_ready()

        error = getattr(exception, "original", exception)

        if hasattr(ctx.command, "on_error"):
            return

        elif isinstance(error, CheckFailure):
            return

        if isinstance(
            error,
            (
                BadUnionArgument,
                CommandOnCooldown,
                PrivateMessageOnly,
                NoPrivateMessage,
                MissingRequiredArgument,
                ConversionError,
            ),
        ):
            return await ctx.send(str(error))

        elif isinstance(error, BotMissingPermissions):
            return await ctx.send(
                "I am missing these permissions to do this command:" f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(error, MissingPermissions):
            return await ctx.send(
                "You are missing these permissions to do this command:" f"\n{self.lts(error.missing_perms)}"
            )

        elif isinstance(error, (BotMissingAnyRole, BotMissingRole)):
            return await ctx.send(
                f"I am missing these roles to do this command:"
                f"\n{self.lts(error.missing_roles or [error.missing_role])}"
            )

        elif isinstance(error, (MissingRole, MissingAnyRole)):
            return await ctx.send(
                f"You are missing these roles to do this command:"
                f"\n{self.lts(error.missing_roles or [error.missing_role])}"
            )

        elif isinstance(error, BadArgument) and ctx.command.name in ("rep", "report"):
            return await ctx.send("Can't find that member. Please try again.")

        else:
            raise error

    """   Functions   """

    async def get_context(self, message, *, cls=SyltesContext):
        """Implementation of custom context"""
        return await super().get_context(message=message, cls=cls or SyltesContext)

    def em(self, **kwargs):
        return discord.Embed(**kwargs)

    @staticmethod
    def lts(list_: list):
        """List to string.
        For use in `self.on_command_error`"""
        return ", ".join([obj.name if isinstance(obj, discord.Role) else str(obj).replace("_", " ") for obj in list_])

    async def resolve_user(self, user_id: int) -> discord.User:
        """Resolve a user from their ID."""

        user = self.get_user(id=user_id)
        if user is None:
            try:
                user = await self.fetch_user(user_id)
            except discord.NotFound:
                return None

        return user

    @classmethod
    async def setup(cls, **kwargs):
        bot = cls()
        try:
            await bot.start(settings.bot.token, **kwargs)
        except KeyboardInterrupt:
            await bot.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Tim.setup())
