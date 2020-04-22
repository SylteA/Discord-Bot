from discord.ext import commands
import discord

from datetime import datetime
import asyncio
import pandas

from config import YOUTUBE_API_KEY, NOTIFICATION_CHANNEL_ID, NOTIFICATION_ROLE_ID
from .utils.checks import in_twt


def to_pages_by_lines(content: str, max_size: int):
    pages = ['']
    i = 0
    for line in content.splitlines(keepends=True):
        if len(pages[i] + line) > max_size:
            i += 1
            pages.append('')
        pages[i] += line
    return pages


class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.data = None
        self.last_video = None
        self.get_videos = self.bot.loop.create_task(self._get_last_video())
        self.youtube_query = self.bot.loop.create_task(self._update_youtube_stats())  # Called every 10 minutes
        self.webhook = self.bot.guild.get_channel(NOTIFICATION_CHANNEL_ID)
        self.NOTIFICATION_ROLE = self.bot.guild.get_role(NOTIFICATION_ROLE_ID)

    def cog_unload(self):
        self.youtube_query.cancel()
        self.get_videos.cancel()

    async def cog_check(self, ctx):
        if self.data is None or self.last_video is None:
            await ctx.send('Currently unavailable. Try again later.')
            return False
        return True

    async def _update_youtube_stats(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            print(f'Querying youtube stats')
            response = await self.bot.session.get(f"https://www.googleapis.com/youtube/v3/channels"
                                                  f"?part=snippet,statistics,contentDetails"
                                                  f"&id=UC4JX40jDee_tINbkjycV4Sg"
                                                  f"&key={YOUTUBE_API_KEY}")
            data = await response.json()

            if self.data is not None:
                videos = data['items'][0]['statistics']['videoCount']
                last_videos = self.data['statistics']['videoCount']
                self.data = data['items'][0]

                if videos != last_videos:
                    print('Getting last video')
                    response = await self.bot.session.get(f'https://www.googleapis.com/youtube/v3/playlistItems'
                                                          f'?part=snippet,statistics'
                                                          f'&maxResults=1'
                                                          f'&channelId=UC4JX40jDee_tINbkjycV4Sg'
                                                          f'&playlistId=UU4JX40jDee_tINbkjycV4Sg'
                                                          f'&key={YOUTUBE_API_KEY}')
                    data = await response.json()
                    self.last_video = data['items'][0]
                    print(f'Finished getting last video, sleeping...')
                    await self.alert_webhook()

            self.data = data['items'][0]
            print(f'Finished querying youtube stats, sleeping...')
            await asyncio.sleep(60*10)

    async def _get_last_video(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            print('Getting last video')
            response = await self.bot.session.get(f'https://www.googleapis.com/youtube/v3/playlistItems'
                                                  f'?part=snippet,statistics'
                                                  f'&maxResults=1'
                                                  f'&channelId=UC4JX40jDee_tINbkjycV4Sg'
                                                  f'&playlistId=UU4JX40jDee_tINbkjycV4Sg'
                                                  f'&key={YOUTUBE_API_KEY}')
            data = await response.json()
            self.last_video = data['items'][0]
            print(f'Finished getting last video, sleeping...')
            await asyncio.sleep(60*10)

    async def alert_webhook(self):
        data = self.last_video['snippet']

        if await self.check_duplicate(data['title']):
            return

        description = to_pages_by_lines(data["description"], max_size=500)[0].replace('*', '').strip()
        url = f'https://www.youtube.com/watch?v={data["resourceId"]["videoId"]}'

        embed = discord.Embed(title=data['title'], url=url,
                              description=description, color=discord.Color.red())

        channelinfo = self.data['snippet']
        embed.set_author(name=channelinfo['title'], url=f'https://www.youtube.com/c/{channelinfo["customUrl"]}')

        avatar = channelinfo['thumbnails']['high']['url']
        embed.set_thumbnail(url=avatar)
        embed.set_image(url=data['thumbnails']['maxres']['url'])
        embed.set_footer(text='Uploaded:', icon_url=avatar)
        embed.timestamp = datetime.strptime(data["publishedAt"], '%Y-%m-%dT%H:%M:%S.%fZ')
        await self.NOTIFICATION_ROLE.edit(mentionable=True)
        await self.webhook.send(content=f'{self.NOTIFICATION_ROLE.mention} New upload!', embed=embed)
        await self.NOTIFICATION_ROLE.edit(mentionable=False)

    async def check_duplicate(self, title: str):
        last_message = await self.webhook.fetch_message(self.webhook.last_message_id)
        if len(last_message.embeds) > 0:
            embed = last_message.embeds[0]
            if embed.title == title:
                return True
        return False

    @commands.group(name='youtube', aliases=['yt', 'search'])
    async def _youtube(self, ctx, *, title: str = None):
        """Youtube related commands"""
        if ctx.invoked_subcommand is None:
            if title is not None:
                return await ctx.invoke(self.bot.get_command('youtube search'), title=title)
            return await ctx.invoke(self.bot.get_command('youtube stats'))

    @_youtube.command()
    async def stats(self, ctx):
        """Get general stats from tims youtube channel"""
        data = self.data
        embed = discord.Embed(title=data['snippet']['title'],
                              description=data['snippet']['description'],
                              color=discord.Color.red())
        embed.set_thumbnail(url=data['snippet']['thumbnails']['high']['url'])
        stats = data['statistics']
        statistics = [('Videos', stats['videoCount']),
                      ('Views', stats['viewCount'])]
        frame = pandas.DataFrame(statistics, columns=('Subscribers', str(stats['subscriberCount'])))
        embed.add_field(name='**Statistics**', value=f"```{frame.head().to_string(index=False)}```", inline=False)
        video = self.last_video['snippet']
        description = to_pages_by_lines(video["description"], max_size=199)[0].replace("*", "").strip()
        url = f'https://www.youtube.com/watch?v={video["resourceId"]["videoId"]}'
        embed.add_field(name='**Last video**', value=f'Title: **{video["title"]}**\n'
                                                     f'Description: *{description}*\n'
                                                     f'Watch it [**here!**]({url})')
        embed.set_image(url=video['thumbnails']['maxres']['url'])
        embed.set_footer(text='Uploaded:', icon_url=data['snippet']['thumbnails']['high']['url'])
        embed.timestamp = datetime.strptime(video["publishedAt"], '%Y-%m-%dT%H:%M:%S.%fZ')
        await ctx.send(embed=embed)

    @_youtube.command(name='search', aliases=['query', 'q', 's'])
    @commands.cooldown(5, 60, commands.BucketType.user)
    @in_twt()
    async def query(self, ctx, *, title):
        """Search for youtube videos titled `title`"""
        async with self.bot.session.get("https://www.googleapis.com/youtube/v3/search"
                                        "?part=snippet"
                                        "&channelId=UC4JX40jDee_tINbkjycV4Sg"
                                        f"&q={title}"
                                        f"&key={YOUTUBE_API_KEY}") as request:
            data = await request.json()
            videos = data['items']
        string = ""
        for index, video in enumerate(videos):
            if video['id']['kind'] == 'youtube#video':
                string += f"[{video['snippet']['title']}](https://youtube.com/watch?v={video['id']['videoId']})\n"
            if index > 8:
                break
        if not len(string) > 0:
            title = f"No videos found D:"
            description = f"There were no videos found with your search"
        else:
            title = f"Video search results"
            description = string
        embed = discord.Embed(title=title, description=description, color=discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(name='subscribe', aliases=['sub'])
    @commands.guild_only()
    @in_twt()
    async def subscribe(self, ctx):
        """Subscribe to new videos from Tims youtube channel"""
        if self.NOTIFICATION_ROLE in ctx.author.roles:
            return await ctx.send('You are already being notified, to unsubscribe use `!unsubscribe`')
        try:
            await ctx.author.add_roles(self.NOTIFICATION_ROLE)
        except discord.HTTPException:
            return await ctx.send('Sorry, cant help you D:')
        else:
            await ctx.send(f'You will now be notified once tim uploads a new video!')

    @commands.command(name='unsubscribe', aliases=['unsub'])
    @commands.guild_only()
    @in_twt()
    async def unsubscribe(self, ctx):
        """Unsubscribe from discord mentions when Tim uploads a new video"""
        if self.NOTIFICATION_ROLE not in ctx.author.roles:
            return await ctx.send('You are not currently subscribed, to subscribe use `!subscribe`')
        try:
            await ctx.author.remove_roles(self.NOTIFICATION_ROLE)
        except discord.HTTPException:
            return await ctx.send('Sorry, cant help you D:')
        else:
            await ctx.send('You will no longer be notified of new videos.')


def setup(bot):
    bot.add_cog(YouTube(bot))
