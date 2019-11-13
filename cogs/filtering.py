from discord.ext import commands
import discord

from urllib.parse import urlparse
import re


class Filtering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._allowed_urls = [
            "hasteb.in", "hastebin", "pastebin", "mystb.in"
            "youtube", "github", "techwithtim"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        await self._do_filtering(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        await self._do_filtering(after)

    async def _do_filtering(self, message: discord.Message):
        urls = re.findall(r"(https?://[^\s]+)", message.content, flags=re.IGNORECASE)
        for url in urls:
            try:
                result = urlparse(url)
                if all([result.scheme, result.netloc]):
                    if not await self._allowed_url(result.netloc):
                        await message.delete()
                        return await message.channel.send(
                            f"```The link you sent is not allowed on this server. {message.author.mention} "
                            f"If you believe this is a mistake contact a staff member.```")
            except Exception as e:
                raise e
                # I dont know what error could be raised, let me know if one occurs please

    async def _allowed_url(self, netloc: str) -> bool:
        """Checks if the provided url `netloc` is an allowed url."""
        for url in self._allowed_urls:
            if url in netloc:
                return True
        return False


def setup(bot):
    bot.add_cog(Filtering(bot))
