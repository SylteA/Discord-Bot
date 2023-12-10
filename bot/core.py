import datetime
import json
import logging
import os
import sys
import traceback
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.config import settings
from bot.models import GuildConfig
from bot.services import http, paste
from bot.services.paste import Document
from utils.errors import IgnorableException
from utils.health import update_health
from utils.time import human_timedelta

log = logging.getLogger(__name__)

os.environ.update(JISHAKU_NO_UNDERSCORE="True", JISHAKU_NO_DM_TRACEBACK="True", JISHAKU_HIDE="True")
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=False)


class DiscordBot(commands.Bot):
    def __init__(self, prefixes: tuple[str, ...], extensions: tuple[str, ...], intents: discord.Intents):
        super().__init__(
            intents=intents, command_prefix=prefixes, case_insensitive=True, allowed_mentions=ALLOWED_MENTIONS
        )
        self.start_time = datetime.datetime.utcnow()
        self.initial_extensions = extensions

        self.error_webhook: discord.Webhook | None = None

    async def resolve_user(self, user_id: int) -> discord.User | None:
        """Resolve a user from their ID."""
        user = self.get_user(user_id)
        if user is None:
            try:
                user = await self.fetch_user(user_id)
            except discord.NotFound:
                return None

        return user

    @property
    def guild(self) -> discord.Guild | None:
        return self.get_guild(settings.guild.id)

    async def setup_hook(self) -> None:
        """Connect DB before bot is ready to assure that no calls are made before its ready"""
        self.loop.create_task(self.when_online())
        self.presence.start()

        update_health("running", True)

        self.tree.on_error = self.on_app_command_error

        self.error_webhook = discord.Webhook.from_url(url=settings.errors.webhook_url, session=http.session)

    async def on_disconnect(self):
        update_health("ready", False)

    async def on_ready(self):
        update_health("ready", True)

    async def when_online(self):
        log.info("Waiting until bot is ready to load extensions and app commands.")
        await self.wait_until_ready()

        await self.load_extensions()
        await self.sync_commands()

    async def load_extensions(self):
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
            except Exception as error:
                log.error(f"Failed to load extension {ext!r}:", exc_info=error)

        log.info(f"Loaded all extensions after {human_timedelta(self.start_time, brief=True, suffix=False)}")

    async def sync_commands(self) -> None:
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

        log.info("Commands synced.")
        log.info(f"Successfully logged in as {self.user}. In {len(self.guilds)} guilds")

    async def on_ready(self):
        query = "SELECT COALESCE(array_agg(guild_id), '{}') FROM guild_configs"

        stored_ids = await GuildConfig.fetchval(query)
        missing_ids = [(guild.id,) for guild in self.guilds if guild.id not in stored_ids]

        if missing_ids:
            query = "INSERT INTO guild_configs (guild_id) VALUES ($1)"
            await GuildConfig.pool.executemany(query, missing_ids)

    async def on_guild_join(self, guild: discord.Guild):
        log.info(f"{self.user.name} has been added to a new guild: {guild.name}")

        query = """INSERT INTO guild_configs (guild_id)
                        VALUES ($1)
                   ON CONFLICT (guild_id)
                            DO NOTHING"""
        await GuildConfig.execute(query, guild.id)

    async def on_message(self, message):
        await self.wait_until_ready()

        if message.author.bot:
            return

        log.debug(f"{message.channel}: {message.author}: {message.clean_content}")

        await self.process_commands(message)

    async def process_commands(self, message: discord.Message, /):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        log.info(f"{ctx.author} invoking command: {ctx.clean_prefix}{ctx.command.qualified_name}")
        await self.invoke(ctx)

    async def send_error(self, content: str, header: str, invoked_details_document: Document = None) -> None:
        def wrap(code: str) -> str:
            code = code.replace("`", "\u200b`")
            return f"```py\n{code}\n```"

        if len(content) > 1024:  # Keeping it short for readability.
            document = await paste.create(content)
            content = wrap(content[:1024]) + f"\n\n [Full traceback]({document.url})"
        else:
            content = wrap(content)

        embed = discord.Embed(
            title=header, description=content, color=discord.Color.red(), timestamp=discord.utils.utcnow()
        )
        if invoked_details_document:
            embed.add_field(name="Command Details: ", value=invoked_details_document.url, inline=True)

        await self.error_webhook.send(embed=embed)

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        content = "".join(traceback.format_exception(*sys.exc_info()))
        header = f"Ignored exception in event method **{event_method}**"

        await self.send_error(content, header)

    async def on_app_command_error(self, interaction: "InteractionType", error: app_commands.AppCommandError):
        """Handle errors in app commands."""

        if isinstance(error.__cause__, IgnorableException):
            return

        if interaction.command is None:
            log.error("Ignoring exception in command tree.", exc_info=error)
            return

        if isinstance(error, app_commands.CheckFailure):
            log.info(f"{interaction.user} failed to use the command {interaction.command.qualified_name}")
            return

        content = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        header = (
            f"Ignored exception in command **{interaction.command.qualified_name}** Invoked by **{interaction.user}** "
            f"in channel **{interaction.channel.name}**"
        )
        invoked_details_document = await paste.create(str(json.dumps(interaction.data, indent=2)))
        await self.send_error(content, header, invoked_details_document)
        log.error("Ignoring unhandled exception", exc_info=error)

    @tasks.loop(hours=24)
    async def presence(self):
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Game(name='use the prefix "tim."'))


InteractionType = discord.Interaction[DiscordBot]
