from discord.ext import commands
import discord

from .utils.checks import is_mod

from urllib.parse import urlparse
import asyncio
import re


class Filtering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.configs = {}

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False

        return is_mod(ctx.author)

    async def assure_config(self, guild_id: int):
        if str(guild_id) not in self.configs:
            config = await self.bot.db.get_config(guild_id)
            self.configs[str(guild_id)] = config

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if not message.guild:
            return

        await self.assure_config(message.guild.id)
        await self._do_filtering(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.wait_until_ready()
        if not before.guild:
            return

        await self.assure_config(after.guild.id)
        await self._do_filtering(after)

    async def _do_filtering(self, message: discord.Message):
        config = self.configs[str(message.guild.id)]
        if not config.enabled:
            return

        urls = re.findall(r"(https?://[^\s]+)", message.content, flags=re.IGNORECASE)
        for url in urls:
            try:
                result = urlparse(url)
                if all([result.scheme, result.netloc]):
                    result = await self._blacklisted_url(result.netloc, guild_id=message.guild.id)
                    if result:
                        if not is_mod(message.author):
                            reply = f"The link you sent is not allowed on this server. {message.author.mention} " + \
                                    f"If you believe this is a mistake contact a staff member."
                            reason = config.has_reason(result)
                            if reason:
                                reply += '\n\n' + reason
                            await message.delete()
                            return await message.channel.send(reply)

            except Exception as e:
                raise e  # I don't know what error could be raised, let me know an error occurs please

    async def _blacklisted_url(self, netloc: str, guild_id: int) -> bool:
        """Checks if the provided netloc is blacklisted."""
        for url in self.configs[str(guild_id)].blacklist_urls:
            if url in netloc:
                return url
        return False

    @commands.group()
    async def filter(self, ctx):
        """Use `filter blacklist` to manage the blacklist
           Use `filter whitelist` to mange the channel whitelist
           Ise `filter toggle` to toggle the filter off"""
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Use `{ctx.prefix}filter blacklist` to manage the blacklist\n'
                           f'Use `{ctx.prefix}filter whitelist` to manage the whitelist\n'
                           f'Use `{ctx.prefix}filter toggle` to toggle the filter.')

    @filter.command()
    async def toggle(self, ctx):
        """Toggle on or off the filter"""
        config = self.configs[str(ctx.guild.id)]
        if config.enabled:
            enabled = 'enabled'
            disable = 'disable'
        else:
            enabled = 'disabled'
            disable = 'enable'

        await ctx.send(f'The filter is currently {enabled} do you want to {disable} it?\n\n'
                       f'Reply with `YES` or `NO`')

        try:
            reply = await self.bot.wait_for('message',
                                            check=lambda m: m.channel == ctx.channel and m.author == ctx.author,
                                            timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send(f'Timed out, doing nothing.')
        print('Got message')

        text = reply.content
        if text.lower() == 'yes':
            continue_ = True
        elif text.lower() == 'no':
            continue_ = False
        else:
            return await ctx.send('Invalid answer.')

        if continue_:
            await config.toggle()
            return await ctx.send(f'Toggled chat filter')
        return await ctx.send(f'Doing nothing.')

    @filter.group()
    async def blacklist(self, ctx):
        """
        Use `filter blacklist add` to add URLs to the blacklist
        Use `filter blacklist remove` to remove URLs from blacklist
        Use `filter blacklist list` to show current blacklisted urls

        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Use `{ctx.prefix}filter blacklist add` to add URLs to the blacklist\n'
                           f'Use `{ctx.prefix}filter blacklist remove` to remove URLs from blacklist\n'
                           f'Use `{ctx.prefix}filter blacklist list` to show current blacklisted urls')

    @blacklist.command()
    async def add(self, ctx, url: str):
        """Add a URL to the filter"""
        config = self.configs[str(ctx.guild.id)]
        if url in config.blacklist_urls:
            return await ctx.send(f'That url is already blacklisted.')

        config.blacklist_urls.append(url)
        await config.update()
        await ctx.send(f'Added {url} to the blacklist.')
        reason = await ctx.prompt_reply(f'Any specific reason for blacklisting this url?\nReply with `no` for no reason')
        if reason is None:
            return await ctx.send(f'Ok, set no reason')
        else:
            if reason.lower() is 'no':
                return await ctx.send(f'Ok, set no reason')
            config.reasons[url] = reason
            await config.update()
            await ctx.send(f'Ok the reason for this blacklist is now: {reason}')

    @blacklist.command()
    async def remove(self, ctx, url: str):
        """Remove a URL from the filter"""
        config = self.configs[str(ctx.guild.id)]
        if url not in config.blacklist_urls:
            return await ctx.send(f'That url is not blacklisted.')

        config.blacklist_urls.remove(url)
        await config.update()
        await ctx.send(f'Removed {url} from the blacklist.')
        if config.has_reason(url):
            del config[url]
            await config.update()

    @blacklist.command()
    async def list(self, ctx):
        """List all blacklisted URLs and reasons why"""
        config = self.configs[str(ctx.guild.id)]
        string = "```"
        for url in config.blacklist_urls:
            string += url
            reason = config.has_reason(url)
            if reason:
                string += f' :reason: {reason}\n'
            else:
                string += ' :: \n'
        await ctx.send(string + '```')

    @filter.group()
    async def whitelist(self, ctx):
        """
        Use `filter whitelist add` to add channels to the whitelist
        Use `filter whitelist remove` to remove channels from whitelist
        Use `filter whitelist list` to show current whitelisted channels
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Use `{ctx.prefix}filter whitelist add` to add channels to the whitelist\n'
                           f'Use `{ctx.prefix}filter whitelist remove` to remove channels from whitelist\n'
                           f'Use `{ctx.prefix}filter whitelist list` to show current whitelisted channels')

    @whitelist.command(name='add')
    async def add_(self, ctx, channel: commands.TextChannelConverter):
        """Add a channel to the URL filter whitelist"""
        config = self.configs[str(ctx.guild.id)]
        if channel.id in config.whitelist_channels:
            return await ctx.send('That channel is already in the whitelist')

        config.whitelist_channels.append(channel.id)
        await config.update()
        await ctx.send(f'Added {channel.name} to the whitelist')

    @whitelist.command(name='remove')
    async def remove_(self, ctx, channel: commands.TextChannelConverter):
        """Remove a channel from the URL filter whitelist"""
        config = self.configs[str(ctx.guild.id)]
        if channel.id not in config.whitelist_channels:
            return await ctx.send('That channel is already not whitelisted')

        config.whitelist_channels.remove(channel.id)
        await config.update()
        await ctx.send(f'Removed {channel.name} from the whitelist')

    @whitelist.command(name='list')
    async def list_(self, ctx):
        """List the whitelisted channels from URL filtering"""
        config = self.configs[str(ctx.guild.id)]
        channels = []
        update = False
        for channel in config.whitelist_channels:
            channel_ = ctx.guild.get_channel(channel)
            if isinstance(channel_, discord.TextChannel):
                channels.append(channel_)
            else:
                config.whitelist_channels.remove(channel)
                update = True
        await ctx.send('```' + '\n'.join(channel.name for channel in channels) + '```')
        if update:
            await config.update()


def setup(bot):
    bot.add_cog(Filtering(bot))
