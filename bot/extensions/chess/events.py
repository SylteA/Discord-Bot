import asyncio
from collections import defaultdict

import discord
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.chess.tasks import ChessTasks


class ChessEvents(commands.Cog):
    """Events for Chess functions"""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.tasks: dict[int, list[tuple[asyncio.Task, discord.ScheduledEvent]]] = defaultdict(list)

    def cog_load(self) -> None:
        for guild in self.bot.guilds:
            for event in guild.scheduled_events:
                if event.location != f"<#{settings.chess.channel_id}>":
                    continue

                if any(e.id == event.id for task, e in self.tasks[guild.id]):
                    continue

                self.tasks[guild.id].append((asyncio.create_task(ChessTasks(self.bot).run_task(event)), event))

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        if event.location != f"<#{settings.chess.channel_id}>":
            return

        self.tasks[event.guild.id].append((asyncio.create_task(ChessTasks(self.bot).run_task(event)), event))

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        if event.location != f"<#{settings.chess.channel_id}>":
            return

        for task, e in self.tasks[event.guild.id]:
            if e.id == event.id:
                task.cancel()
                self.tasks[event.guild.id].remove((task, e))
                break

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        if before.location != f"<#{settings.chess.channel_id}>":
            return

        for task, e in self.tasks[before.guild.id]:
            if e.id == before.id:
                if after.location.startswith("https://lichess.org/swiss/"):
                    self.tasks[before.guild.id].remove((task, e))
                    break

                task.cancel()
                self.tasks[before.guild.id].remove((task, e))

                if after.location != f"<#{settings.chess.channel_id}>":
                    return

                self.tasks[before.guild.id].append((asyncio.create_task(ChessTasks(self.bot).run_task(after)), after))
                break
