from discord.ext import commands
import discord

from .utils.DataBase.tag import Tag
from .utils.checks import is_mod_check

class TagCommands(commands.Cog, name="Tags"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tag(self, name:str):
        tag = Tag.fetch(bot, ctx.guild.id, ctx.author.id, name)
        if not tag:
            embed = discord.Embed(title="Error!", description="""```
            Tag was not found
            ```""")
        else:
            embed = discord.Embed(title="Tag {0.capitalize()}".format(tag.name), description=tag.text)
        await ctx.send(embed)

    @tag.command()
    @is_mod_check()
    async def create(self, ctx, name:str, *, text:str):
        name = lower(name)
        tag = Tag(bot, ctx.guild.id, ctx.author.id, text, name)
        try:
            tag.post()
            embed = discord.Embed(title="Tag created!", description="You have sucsessfully created the tag ")
        except BaseException as error:
            embed = discord.Embed(title="Error!", description="""```
            {}
            ```""".format(str(error)))
        await ctx.send(embed=embed)

    @tag.command()
    @is_mod_check()
    async def edit(self, ctx, name:str, *, text:str):
        name = lower(name)
        tag = Tag.fetch(bot, ctx.guild.id, ctx.author.id, name)
        if not tag:
            embed = discord.Embed(title="Error!", description="""```
            Tag was not found.
            ```""")
        else:
            try:
                tag.update(text)
                embed = discord.Embed(title="Tag edited!", description="You have sucsessfully edited the tag.")
            except BaseException as error:
                embed = discord.Embed(title="Error!", description="""```
                {}
                ```""".format(str(error)))
        await ctx.send(embed=embed)

    @tag.command()
    @is_mod_check()
    async def delete(self, ctx, name:str):
        name = lower(name)
        tag = Tag.fetch(bot, ctx.guild.id, ctx.author.id, name)
        if not tag:
            embed = discord.Embed(title="Error!", description="""```
            Tag was not found.
            ```""")
        else:
            try:
                tag.delete()
                embed = discord.Embed(title="Tag delete!", description="You have sucsessfully deleted the tag")
            except BaseException as error:
                embed = discord.Embed(title="Error!", description="""```
                {}
                ```""".format(str(error)))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Tag())