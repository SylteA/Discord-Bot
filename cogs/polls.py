from discord.ext import commands
import discord

import asyncio

from .utils.DataBase.poll import Poll
from .utils.checks import is_mod


class SyltesPolls(commands.Cog, name="Polls"):
    def __init__(self, bot):
        self.bot = bot
        self.polls = {}
        self.listeners = {}

    def cog_unload(self):
        asyncio.create_task(self._cleanup_polls())

    async def _cleanup_polls(self):
        for poll in self.listeners:
            if poll is not None:
                await poll.stop

    async def cog_check(self, ctx):
        if ctx.guild is None:
            return

        return is_mod(ctx.author)

    async def cog_before_invoke(self, ctx):
        if self.polls.get(str(ctx.guild.id), False) is False:
            poll = await self.bot.db.get_current_poll(ctx.guild.id)
            self.polls[str(ctx.guild.id)] = poll
            if isinstance(poll, Poll):
                if str(ctx.guild.id) not in self.listeners:
                    self.listeners[str(ctx.guild.id)] = await poll.listen()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return

        if self.polls.get(str(payload.guild_id), False) is False:
            poll = await self.bot.db.get_current_poll(payload.guild_id)
            self.polls[str(payload.guild_id)] = poll
            if isinstance(poll, Poll):
                if str(payload.guild_id) not in self.listeners:
                    self.listeners[str(payload.guild_id)] = await poll.listen()
                    await poll.handle_payload(payload)

    @commands.group(hidden=True)  # TODO: Fix // find out why this malfunctioned
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(self.bot.get_command('poll new'))

    @staticmethod
    async def cleanup(messages: list):
        await asyncio.sleep(5)
        for message in messages:
            try:
                await message.delete()
            except (discord.Forbidden, TypeError):
                pass

    async def _end_active_poll(self, guild_id: int):
        for g_id, poll in zip(self.listeners.keys(), self.listeners.values()):
            if g_id == str(guild_id):
                if poll is not None:
                    await poll.stop()

    @poll.command()
    async def new(self, ctx, *, description: str):
        if not is_mod(ctx.author):
            return
        to_clean = []
        poll = Poll(bot=self.bot, guild_id=ctx.guild.id, author_id=ctx.author.id, channel_id=ctx.channel.id,
                    message_id=0, description=description, options={}, replies={}, created_at=ctx.message.created_at)
        msg = await ctx.send(f'What options do you want your poll to have?\n'
                             f'Reply with one option at a time\n'
                             f'Type **`break`** to stop')
        to_clean.extend((msg, ctx.message))
        while True:
            try:
                message = await self.bot.wait_for('message', timeout=30,
                                                  check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
            except asyncio.TimeoutError:
                if len(poll.options) == 0:
                    to_clean.append(await ctx.send(f'Timed out, doing nothing.'))
                    return await self.cleanup(to_clean)
                break
            to_clean.append(message)
            content = await self.bot.clean_text.convert(ctx, message.content)
            if content == 'break':
                break
            poll.options[str(len(poll.options) + 1)] = content
            if len(poll.options) >= 10:
                await ctx.send(f'You have reached the maximum of 10 options.')
                break

        msg = await ctx.send(f'Are you sure you want to post this poll?\n\n'
                             f'Reply with `YES` to post, `NO` to return.')
        to_clean.extend((msg, await poll.display(ctx)))
        try:
            message = await self.bot.wait_for('message', timeout=30,
                                              check=lambda m: m.channel == ctx.channel and m.author == ctx.author)
            to_clean.append(message)
        except asyncio.TimeoutError:
            to_clean.append(await ctx.send(f'Timed out, doing nothing.'))
            await self.cleanup(to_clean)
            return
        content = await self.bot.clean_text.convert(ctx, message.content)
        if content.lower() == 'yes':
            asyncio.ensure_future(self.cleanup(to_clean), loop=self.bot.loop)
            message = await poll.display(ctx)
            await self._end_active_poll(ctx.guild.id)
            poll.message_id = message.id
            await poll.listen()
            await poll.post()
            await ctx.send(f'Poll posted, cleaning up...', delete_after=4)
        else:
            to_clean.append(await ctx.send('Okay then, cleaning up...'))
            return await self.cleanup(to_clean)


def setup(bot):
    bot.add_cog(SyltesPolls(bot))

