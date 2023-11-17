import re
import xml.etree.ElementTree as ET
from datetime import datetime

import discord
from discord.ext import commands, tasks
from pydantic import BaseModel

from bot import core
from bot.config import settings
from bot.services import http

YOUTUBE_URL = re.compile(r"(?P<url>https?://www\.youtube\.com/watch\?v=[\w-]+)")
RSS_FEED_BASE_URL = "https://www.youtube.com/feeds/videos.xml"


class Video(BaseModel):
    link: str
    title: str
    published: str
    description: str
    thumbnail: str


class YoutubeTasks(commands.Cog):
    """Tasks for YouTube functions"""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot
        self.video_links: list[str] = []
        self.old_thumbnails: list[tuple[discord.Message, str]] = []
        self.check_for_new_videos.start()

    def cog_unload(self) -> None:
        self.check_for_new_videos.cancel()

    @property
    def channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.youtube.text_channel_id)

    @tasks.loop(minutes=2)
    async def check_for_new_videos(self):
        """Checks old thumbnails for higher resolution images and looks for new videos"""
        await self.check_old_thumbnails()
        await self.find_new_videos()

    @check_for_new_videos.error
    async def on_check_error(self, error: Exception):
        """Logs any errors that occur during the check_for_new_videos task"""
        await self.bot.on_error("check_for_new_videos", error)

    @check_for_new_videos.before_loop
    async def before_check(self):
        """Fetches the 10 last videos posted so we don't accidentally re-post it."""
        if self.video_links:
            return

        async for message in self.channel.history(limit=10):
            if message.embeds:
                embed = message.embeds[0]
                self.video_links.append(embed.url)
                if message.author == self.bot.user and embed.image.url.endswith("/mqdefault.jpg"):
                    self.old_thumbnails.append((message, embed.image.url))

            else:
                match = YOUTUBE_URL.search(message.content)
                if match:
                    self.video_links.append(match.group("url"))

    async def check_old_thumbnails(self):
        """Tries to fetch new thumbnails for any videos we've posted with a low resolution thumbnail."""
        for message, thumbnail_url in self.old_thumbnails:
            max_resolution = thumbnail_url.replace("/mqdefault.jpg", "/maxresdefault.jpg")

            if not await self.image_exists(max_resolution):
                continue

            embed = message.embeds[0]
            embed.set_image(url=thumbnail_url)
            await message.edit(embed=embed)

            self.old_thumbnails.remove((message, thumbnail_url))

    async def find_new_videos(self):
        """Fetches most recent videos from rss feed and publishes any new videos."""
        url = RSS_FEED_BASE_URL + "?channel_id=" + settings.youtube.channel_id

        async with http.session.get(url) as response:
            data = await response.text()
            tree = ET.fromstring(data)
            ns = "{http://www.w3.org/2005/Atom}"
            md = "{http://search.yahoo.com/mrss/}"

            entry = tree.find(ns + "entry")
            media_group = entry.find(md + "group")
            video = Video(
                link=entry.find(ns + "link").attrib["href"],
                title=entry.find(ns + "title").text,
                published=entry.find(ns + "published").text,
                description=media_group.find(md + "description").text,
                thumbnail=media_group.find(md + "thumbnail").attrib["url"].replace("/hqdefault.jpg", "/mqdefault.jpg"),
            )

        if video.link in self.video_links:
            return

        self.video_links.append(video.link)
        await self.send_notification(video)

    async def send_notification(self, video: Video) -> None:
        """Sends an embed to discord with the new video."""
        max_resolution = video.thumbnail.replace("/mqdefault.jpg", "/maxresdefault.jpg")
        use_max_resolution = await self.image_exists(max_resolution)

        if use_max_resolution:
            video.thumbnail = max_resolution

        embed = discord.Embed(
            title=video.title,
            description=video.description.split("\n\n")[0],
            url=video.link,
            color=discord.Color.red(),
            timestamp=datetime.strptime(video.published, "%Y-%m-%dT%H:%M:%S%z"),
        )
        embed.set_image(url=video.thumbnail)
        embed.set_author(
            name="Tech With Tim",
            url="https://www.youtube.com/c/TechWithTim",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_footer(text="Uploaded", icon_url=self.bot.user.display_avatar.url)

        message = await self.channel.send(
            content=f"Hey <@&{settings.youtube.role_id}>, **Tim** just posted a video! Go check it out!",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        if not use_max_resolution:
            self.old_thumbnails.append((message, video.thumbnail))

    @staticmethod
    async def image_exists(url: str):
        async with http.session.head(url) as response:
            return response.status == 200
