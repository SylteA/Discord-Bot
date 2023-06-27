import re
import typing as t

import discord
from discord import app_commands
from discord.ext import commands

from bot import core
from bot.extensions.readthedocs import utils
from bot.services import http


class ReadTheDocs(commands.Cog):
    """New slash commands for documentation."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

        self.page_types = {
            "discord.py": "https://discordpy.readthedocs.io/en/latest",
            "aiohttp": "https://docs.aiohttp.org/en/stable",
            "python": "https://docs.python.org/3",
        }

        self.cache = {}

    async def cog_load(self) -> None:
        """TODO: Populate caches passively on load."""
        await self.build_docs_lookup_table()

    async def build_docs_lookup_table(self) -> None:
        """Fetches, parses and caches the sphinx object inventories for our docs."""
        cache = {}

        for key, page in self.page_types.items():
            async with http.session.get(page + "/objects.inv") as resp:
                data = await resp.read()

                if resp.status != 200:
                    cache[key] = {"status": resp.status, "message": "Failed to fetch objects.", "response": data}
                else:
                    stream = utils.SphinxObjectFileReader(data)
                    cache[key] = {"status": resp.status, "response": utils.parse_object_inv(stream, page)}

        self.cache = cache

    @app_commands.command()
    @app_commands.describe(search="Search term", docs="Documentation")
    async def docs(
        self,
        interaction: core.InteractionType,
        search: str,
        docs: t.Literal["discord.py", "aiohttp", "python"] = "discord.py",
    ):
        """Gives you documentation for the specified entity."""
        if self.cache.get(docs) is None:
            return await interaction.response.send_message(
                "Cache has not been built yet, please try again later...", ephemeral=True
            )

        if self.cache[docs]["status"] != 200:
            return await interaction.response.send_message(self.cache[docs]["message"])

        obj = re.sub(r"^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)", r"\1", search)

        if docs == "discord.py":
            q = obj.lower()  # Point the abc.Messageable types properly:
            for name in dir(discord.abc.Messageable):
                if name[0] == "_":
                    continue
                elif q == name:
                    obj = f"abc.Messageable.{name}"
                    break

        cache = list(self.cache[docs]["response"].items())
        matches = utils.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        if len(matches) == 0:
            return await interaction.response.send_message("Could not find anything, sorry.")

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f"{docs} search results", url=self.page_types[docs])
        embed.description = "\n".join(f"[`{key}`]({url})" for key, url in matches)
        return await interaction.response.send_message(embed=embed)
