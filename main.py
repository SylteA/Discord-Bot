#!/usr/bin/env python3

from discord.ext import commands
import discord

import datetime
import pathlib
import asyncio
import json

from cogs.utils.time import human_timedelta
from cogs.utils.database import DataBase


with open('tokens.json') as json_file:
    data = json.load(json_file)
TOKEN = data["token"]


class Tim(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix='tim.', case_insensitive=True, **kwargs)
        self.start_time = datetime.datetime.utcnow()
        self.db = DataBase()

    """  Events   """

    async def on_ready(self):
        print(f'Successfully logged in as {self.user}\nSharded to {len(self.guilds)} guilds')
        self.guild = self.get_guild(501090983539245061)
        self.welcomes = self.guild.get_channel(511344843247845377)
        await self.change_presence(activity=discord.Game(name='use the prefix "tim"'))
        await self.load_extensions()

    async def on_member_join(self, member):
        if member.guild.id == 501090983539245061:
            await self.welcomes.send(f"Welcome to the Tech With Tim Community {member.mention}!\n"
                                     f"Members += 1\nCurrent # of members: {self.guild.member_count}")

    async def on_message(self, message):
        print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
        if message.author.bot or not message.guild:
            return

        self.db.update_server_stats()
        self.db.update_messages(message.author)
        await self.process_commands(message)

    async def process_commands(self, message):
        if message.author.bot:
            return

        ctx = await self.get_context(message=message)

        if ctx.command is None:
            return

        if ctx.command.name in ('help', 'scoreboard', 'rep_scoreboard', 'reps', 'member_count', 'top_user', 'users',
                                'server_messages', 'messages'):
            if ctx.channel.id not in (511344208955703306, 536199577284509696):
                return await message.channel.send("**Please use #bot-commands channel**")

        await self.invoke(ctx)

    """   Functions   """

    @staticmethod
    def is_mod(member: discord.Member) -> bool:
        for role in member.roles:
            if role.name.lower() in ('helper', 'mod', 'admin', 'tim'):
                return True
        return False

    async def load_extensions(self):
        """Loads all extensions in Path('./cogs')"""
        for extension in [file.stem for file in pathlib.Path('./cogs').glob('*.py')]:
            self.load_extension(f'cogs.{extension}')
        print(f'Loaded all extensions after {human_timedelta(self.start_time, brief=True, suffix=False)}')

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
