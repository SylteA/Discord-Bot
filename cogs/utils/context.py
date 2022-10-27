import asyncio
from typing import Union

import discord
from discord.ext import commands

from config import settings

from ..youtube import to_pages_by_lines


def embed_to_string(embed: discord.Embed) -> str:
    """Convert a embed to a string"""
    string = ""
    if embed.author:
        string = f"{embed.author.name}\n"
    if embed.title:
        string += f"{embed.title}\n"
    if embed.description:
        string += f"{embed.description}\n"
    for field in embed.fields:
        string += f"{field.title}\n{field.value}\n"
    if embed.footer:
        string += f"{embed.footer}"
    return string


class SyltesContext(commands.Context):
    async def send(self, content=None, **kwargs) -> Union[discord.Message, None]:
        """Better handling of missing permissions"""
        embed = kwargs.get("embed")
        embeds = kwargs.get("embeds", [embed] if embed is not None else None)
        file = kwargs.get("file")
        files = kwargs.get("files", [file] if embed is not None else None)
        destination = self.channel
        if self.guild:
            permissions = self.channel.permissions_for(self.guild.me)
            if not permissions.send_messages:
                try:
                    destination = self.author
                    await destination.send(f"I was missing permissions to send messages in {self.channel.mention}.")
                except discord.Forbidden:
                    pass

            if not permissions.embed_links and embeds is not None:
                for embed in embeds:
                    string = embed_to_string(embed)
                    pages = to_pages_by_lines(string, max_size=1900)
                    for page in pages:
                        await destination.send(page)
                kwargs["embeds"] = None

            if not permissions.attach_files and files is not None:
                await destination.send(f"Missing permission to send files in {self.channel.mention}\nCheck your DMs")
                await self.author.send(files=files)
                return

        return await destination.send(content, **kwargs)

    @staticmethod
    async def cleanup(*messages, delay: float = 0.0) -> None:
        """Shortcut for deleting messages, with optional delay param"""

        async def do_deletion(msg):
            await asyncio.sleep(delay)
            try:
                await msg.delete()
            except discord.Forbidden:
                pass

        for message in messages:
            asyncio.ensure_future(do_deletion(message))

    async def prompt_reply(self, message: str, *, timeout=60.0, delete_after=True, author_id=None) -> Union[str, None]:
        """Prompt a text reply from `author_id` if no response is found returns a empty string"""

        author_id = author_id or self.author.id
        _msg = await super().send(message)

        def check(msg):
            return msg.author.id == author_id and msg.channel == self.channel

        try:
            message = await self.bot.wait_for("message", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            await self.send("Timed out.")
            return None

        try:
            if delete_after:
                asyncio.ensure_future(self.cleanup(message, self.message, _msg), loop=self.bot.loop)
        finally:
            if message.content:
                return message.content
            else:
                return None

    async def em(self, delete_after=None, **kwargs):
        """Shortcut to send embeds with `bot.em`"""

        return await self.send(embed=self.bot.em(**kwargs), delete_after=delete_after)

    async def send_help(self, *args):
        """No more cheating on getting help from other channels :P"""
        if self.command.name in (
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
            if self.channel.id not in settings.bot.commands_channels_ids:
                return await self.send("**Please use #bot-commands channel**")
        return await super().send_help(*args)
