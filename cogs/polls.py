from discord.ext import commands
import discord

import asyncio

from .utils.DataBase.poll import Poll


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
                poll.cancel()

    @property
    def reactions(self) -> dict:
        return {
            '1️⃣': '1',
            '2️⃣': '2',
            '3️⃣': '3',
            '4️⃣': '4',
            '5️⃣': '5',
            '6️⃣': '6',
            '7️⃣': '7',
            '8️⃣': '8',
            '9️⃣': '9',
            '🔟': '10'
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id:
            return

        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message.author != self.bot.user:
            return

        if self.polls.get(str(payload.message_id), False) is False:
            poll = await self.bot.db.get_poll(payload.guild_id, payload.message_id)
            self.polls[str(payload.message_id)] = poll
            if isinstance(poll, Poll):
                if str(payload.message_id) not in self.listeners:
                    self.listeners[str(payload.message_id)] = await poll.listen()
                    await poll.handle_payload(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or payload.user_id == self.bot.user.id:
            return

        poll = await self.bot.db.get_poll(payload.guild_id, payload.message_id)
        if poll is not None:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            react = False
            user = self.bot.get_user(payload.user_id)
            for reaction in message.reactions:
                users = await reaction.users().flatten()
                if user in users:
                    react = True

            if not react:
                del poll.replies[str(payload.user_id)]
                await poll._update()

    @commands.group()
    async def poll(self, ctx):
        """ Poll"""
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

    @poll.command()
    async def new(self, ctx, *, description: str):
        """ Create a new Poll """
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
            message.add_reaction("<:tickk:582492589152927782>")
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
            poll.message_id = message.id
            await poll.listen()
            await poll.post()
            await ctx.send('Poll posted, cleaning up...', delete_after=4.0)
        else:
            to_clean.append(await ctx.send('Okay then, cleaning up...'))
            return await self.cleanup(to_clean)


def setup(bot):
    bot.add_cog(SyltesPolls(bot))

