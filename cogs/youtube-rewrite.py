from discord.ext.commands import Cog
from discord.ext import commands
import discord
import asyncio
from discord.ext import tasks
from aiohttp import request
import xml.etree.ElementTree as ET
import aiofiles
import json
from datetime import datetime
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


class Youtube(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook = self.bot.guild.get_channel(NOTIFICATION_CHANNEL_ID)
        self.NOTIFICATION_ROLE = self.bot.guild.get_role(NOTIFICATION_ROLE_ID)
        self._get_last_video.start()  #Check for new in every two minutes
    
    def cog_unload(self):
        self._get_last_video.stop()

    async def savetoJson(self, video, filename):
        async with aiofiles.open(f"{filename}.json", 'w') as jsonfile:
            await jsonfile.write(json.dumps(video))

    async def _get_stored_video(self,filename):
        try:
            async with aiofiles.open(f"{filename}.json","r") as jsonfile:
                    video=dict()
                    resp=await jsonfile.read()
                    video=json.loads(resp)
                    return video
        except:
            return None

    @tasks.loop(seconds=120.0)
    async def _get_last_video(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
        
        url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UC4JX40jDee_tINbkjycV4Sg'
        try:
            async with request("GET",url) as resp:
                data = resp.content
                with open('channelFeed.xml', 'wb') as f:
                    f.write(await data.read())
        except:
            print("AN ERROR OCCURED WHILE FETCHING THE YOUTUBE XML")
            return
        tree = ET.parse('channelFeed.xml')
        videoitems = []
        ns = '{http://www.w3.org/2005/Atom}'
        md = '{http://search.yahoo.com/mrss/}'
        for entry in tree.findall(ns + "entry"):
            video = {}
            url = entry.find(ns+"link")
            video["video_url"] = url.attrib["href"]
            title = entry.find(ns+"title")
            video["title"] = f"{title.text}"
            date_str=str(entry.find((ns+"published")).text)
            video["time"] = date_str

            for mediagroup in entry.findall(md + 'group'):
                thumbnail = mediagroup.find(md + 'thumbnail')
                video['image'] = thumbnail.attrib['url']
                description = mediagroup.find(md + 'description')
                video['description'] = description.text

            videoitems.append(video)
            break
        new_video = videoitems[0]
        video = await self._get_stored_video("videos")

        if video == None:
            await self.savetoJson(new_video, "videos")
            return

        if video['video_url']!=new_video['video_url']:
            print("new") #debug message let it be there
            description = to_pages_by_lines(new_video["description"], max_size=500)[0].replace('*', '').strip()
            embed = discord.Embed(title=new_video['title'],
                                    url=new_video['video_url'],
                                    description=description,
                                    color=discord.Colour.red(),
                                    timestamp=datetime.strptime(new_video["time"], '%Y-%m-%dT%H:%M:%S%z'))
            url = new_video["image"]
            embed.set_image(url=url)
            embed.set_thumbnail(url=self.bot.guild.icon_url)
            embed.set_author(name="Tech With Tim", url="https://www.youtube.com/c/TechWithTim/featured",
                                icon_url=self.bot.guild.icon_url)
            embed.set_footer(text='Uploaded:', icon_url=self.bot.guild.icon_url)
            await self.NOTIFICATION_ROLE.edit(mentionable=True)
            await self.webhook.send(content=f'{self.NOTIFICATION_ROLE.mention} New upload!', embed=embed)
            await self.savetoJson(new_video, "videos")
            await self.NOTIFICATION_ROLE.edit(mentionable=False)
            return

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
    bot.add_cog(Youtube(bot))

    