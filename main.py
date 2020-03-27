#!/usr/bin/env python3
from discord.ext.commands.errors import *
from discord.ext import commands
import discord

from aiohttp import ClientSession
import datetime
import asyncio

from cogs.utils.context import SyltesContext
from cogs.utils.time import human_timedelta
from cogs.utils.DataBase import DataBase, Message, User

from config import TOKEN, POSTGRES

initial_cogs = [
    'cogs.commands',
    'cogs.filtering',
    'cogs.polls',
    'cogs.youtube',
    'cogs.debugging',
    'cogs._help',
    'cogs.tags',
    'cogs.challenges'
]

print('Connecting...')


class Tim(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=kwargs.pop('command_prefix', ('t.', 'tim.')), case_insensitive=True, **kwargs)
        self.session = ClientSession(loop=self.loop)
        self.start_time = datetime.datetime.utcnow()
        self.clean_text = commands.clean_content(escape_markdown=True, fix_channel_mentions=True)

    """  Events   """

    async def on_connect(self):
        """Connect DB before bot is ready to assure that no calls are made before its ready"""
        self.db = await DataBase.create_pool(bot=self, uri=POSTGRES, loop=self.loop)

    async def on_ready(self):
        print(f'Successfully logged in as {self.user}\nSharded to {len(self.guilds)} guilds')
        self.guild = self.get_guild(501090983539245061)
        self.welcomes = self.guild.get_channel(511344843247845377)
        await self.change_presence(activity=discord.Game(name='use the prefix "tim"'))

        for ext in initial_cogs:
            self.load_extension(ext)
        print(f'Loaded all extensions after {human_timedelta(self.start_time, brief=True, suffix=False)}')

    async def on_member_join(self, member):
        await self.wait_until_ready()
        if member.guild.id == 501090983539245061:
            await self.welcomes.send(f"Welcome to the Tech With Tim Community {member.mention}!\n"
                                     f"Members += 1\nCurrent # of members: {self.guild.member_count}")

    async def on_message(self, message):
        await self.wait_until_ready()
        if message.author.bot:
            return
        print(f"{message.channel}: {message.author}: {message.clean_content}")
        if not message.guild:
            return
        await self.process_commands(message)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message=message)

        if ctx.command is None:
            return await Message.on_message(bot=self, message=message)

        if ctx.command.name in ('help', 'scoreboard', 'rep_scoreboard', 'reps', 'member_count', 'top_user', 'users',
                                'server_messages', 'messages'):
            if ctx.channel.id not in (511344208955703306, 536199577284509696):
                return await message.channel.send("**Please use #bot-commands channel**")

        try:
            await self.invoke(ctx)
        finally:
            await User.on_command(bot=self, user=message.author)

    async def on_command_error(self, ctx, exception):
        await self.wait_until_ready()

        error = getattr(exception, 'original', exception)

        if hasattr(ctx.command, 'on_error'):
            return

        elif isinstance(error, CheckFailure):
            return

        if isinstance(error, (BadUnionArgument, CommandOnCooldown, PrivateMessageOnly,
                              NoPrivateMessage, MissingRequiredArgument, ConversionError)):
            return await ctx.send(str(error))

        elif isinstance(error, BotMissingPermissions):
            return await ctx.send('I am missing these permissions to do this command:'
                                  f'\n{self.lts(error.missing_perms)}')

        elif isinstance(error, MissingPermissions):
            return await ctx.send('You are missing these permissions to do this command:'
                                  f'\n{self.lts(error.missing_perms)}')

        elif isinstance(error, (BotMissingAnyRole, BotMissingRole)):
            return await ctx.send(f'I am missing these roles to do this command:'
                                  f'\n{self.lts(error.missing_roles or [error.missing_role])}')

        elif isinstance(error, (MissingRole, MissingAnyRole)):
            return await ctx.send(f'You are missing these roles to do this command:'
                                  f'\n{self.lts(error.missing_roles or [error.missing_role])}')

        else:
            raise error

    """   Functions   """

    async def get_context(self, message, *, cls=SyltesContext):
        """Implementation of custom context"""
        return await super().get_context(message=message, cls=cls or SyltesContext)

    @staticmethod
    def lts(list_: list):
        """List to string.
           For use in `self.on_command_error`"""
        return ', '.join([obj.name if isinstance(obj, discord.Role) else str(obj).replace('_', ' ') for obj in list_])

    @classmethod
    async def setup(cls, **kwargs):
        bot = cls()
        try:
            await bot.start(TOKEN, **kwargs)
        except KeyboardInterrupt:
            await bot.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Tim.setup())
