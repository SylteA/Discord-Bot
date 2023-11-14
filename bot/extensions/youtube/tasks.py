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
        self.update_thumbnail = []
        self.check_for_new_videos.start()

    def cog_unload(self) -> None:
        self.check_for_new_videos.cancel()

    @property
    def channel(self) -> discord.TextChannel | None:
        return self.bot.get_channel(settings.notification.channel_id)

    async def send_notification(self, video: Video) -> None:
        update_thumbnail = False
        max_res = video.thumbnail.replace("/hqdefault.jpg", "/maxresdefault.jpg")
        async with http.session.get(max_res) as response:
            if response.status == 200:
                video.thumbnail = max_res
            else:
                update_thumbnail = True
                video.thumbnail = video.thumbnail.replace("/hqdefault.jpg", "/mqdefault.jpg")

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
            content=f"Hey <@&{settings.notification.role_id}>, **Tim** just posted a video! Go check it out!",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        if update_thumbnail:
            self.update_thumbnail.append((message.id, video.thumbnail))

    @tasks.loop(minutes=2)
    async def check_for_new_videos(self):
        """Check for new videos"""

        for message_id, thumbnail_url in self.update_thumbnail:
            async with http.session.get(thumbnail_url.replace("/mqdefault.jpg", "/maxresdefault.jpg")) as response:
                if response.status == 404:
                    continue

            message = await self.channel.fetch_message(message_id)
            embed = message.embeds[0]
            embed.set_image(url=thumbnail_url)
            await message.edit(embed=embed)
            self.update_thumbnail.remove((message_id, thumbnail_url))

        url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4JX40jDee_tINbkjycV4Sg"
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
                thumbnail=media_group.find(md + "thumbnail").attrib["url"],
            )

        if video.link in self.video_links:
            return

        self.video_links.append(video.link)
        await self.send_notification(video)

    @check_for_new_videos.before_loop
    async def before_check(self):
        if not self.video_links:
            async for message in self.channel.history(limit=10):
                if message.embeds:
                    self.video_links.append(message.embeds[0].url)
                else:
                    match = YOUTUBE_URL.search(message.content)
                    if match:
                        self.video_links.append(match.group("url"))

            self.video_links.reverse()
