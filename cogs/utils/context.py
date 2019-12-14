from discord.ext import commands
import discord

from typing import Union
import asyncio

from ..youtube import to_pages_by_lines


def embed_to_string(embed: discord.Embed) -> str:
    """Convert a embed to a string"""
    string = ""
    if embed.author:
        string = f'{embed.author.name}\n'
    if embed.title:
        string += f'{embed.title}\n'
    if embed.description:
        string += f'{embed.description}\n'
    for field in embed.fields:
        string += f'{field.title}\n{field.value}\n'
    if embed.footer:
        string += f'{embed.footer}'
    return string


class SyltesContext(commands.Context):

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None) \
            -> Union[discord.Message, None]:
        """Better handling of missing permissions"""
        destination = self.channel
        if self.guild:
            permissions = self.guild.me.permissions_in(self.channel)
            if not permissions.send_messages:
                try:
                    destination = self.author
                    await destination.send(f'I was missing permissions to send messages in {self.channel.mention}.')
                except discord.Forbidden:
                    pass
            if not permissions.embed_links and embed is not None:
                string = embed_to_string(embed)
                pages = to_pages_by_lines(string, max_size=1900)
                for page in pages:
                    await destination.send(page)
                embed = None
            if not permissions.attach_files and (file or files):
                await destination.send(f'Missing permission to send files in {self.channel.mention}\nCheck your DMs')
                files = files or [file]
                for file in files:
                    await self.author.send(file=file)
                return
            return await destination.send(content=content, tts=tts, embed=embed, file=file)

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
            message = await self.bot.wait_for('message', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            await self.send('Timed out.')
            return None

        try:
            if delete_after:
                asyncio.ensure_future(self.cleanup(message, self.message, _msg), loop=self.bot.loop)
        finally:
            if message.content:
                return message.content
            else:
                return None
