from discord.ext import commands
import discord


from .utils.DataBase.tag import Tag
from .utils.checks import is_mod_check, is_admin


def setup(bot):
    bot.add_cog(TagCommands(bot=bot))


class TagCommands(commands.Cog, name="Tags"):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if ctx.guild is None:
            return False
        return True

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, name: str):
        """Main tag group."""
        name = name.lower()
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            return await ctx.send('Could not find a tag with that name.')

        await ctx.send("{}".format(tag.text))
        await self.bot.db.execute("UPDATE tags SET uses = uses + 1 WHERE guild_id = $1 AND name = $2",
                                  ctx.guild.id, name)

    @tag.command()
    async def info(self, ctx, *, name: str):
        """Get information regarding the specified tag."""
        name = name.lower()
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            return await ctx.send('Could not find a tag with that name.')

        author = self.bot.get_user(tag.creator_id)
        author = str(author) if isinstance(author, discord.User) else "(ID: {})".format(tag.creator_id)
        text = "Tag: {name}\n\n```prolog\nCreator: {author}\n   Uses: {uses}\n```"\
            .format(name=name, author=author, uses=tag.uses)
        await ctx.send(text)

    @tag.command()
    @is_mod_check()
    async def create(self, ctx, name: str, *, text: str):
        """Create a new tag."""
        text = await commands.clean_content().convert(ctx=ctx, argument=text)
        name = name.lower()

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=text)
        if tag is not None:
            return await ctx.send('A tag with that name already exists.')

        tag = Tag(bot=self.bot, guild_id=ctx.guild.id,
                  creator_id=ctx.author.id, name=name, text=text)
        await tag.post()
        await ctx.send('You have successfully created your tag.')

    @tag.command()
    @is_mod_check()
    async def list(self, ctx):
        """List your existing tags."""
        query = """SELECT name FROM tags WHERE guild_id = $1 AND creator_id = $2"""
        records = await self.bot.db.fetch(query, ctx.guild.id, ctx.author.id)
        if not len(records) >= 1:
            return await ctx.send('You don\'t have any tags?')
        tags = [record["name"] for record in records]
        await ctx.send('{}'.format('\n'.join(tags)))

    @tag.command()
    @is_mod_check()
    async def edit(self, ctx, name: str, *, text: str):
        """Edit a tag"""
        text = await commands.clean_content().convert(ctx=ctx, argument=text)
        name = name.lower()

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)
        if tag is None:
            return await ctx.send('Could not find a tag with that name.')

        await tag.update(text=text)
        await ctx.send('You have successfully edited your tag.')

    @tag.command()
    @is_mod_check()
    async def delete(self, ctx, *, name: str):
        """Delete a tag."""
        name = name.lower()

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            return await ctx.send('Could not find a tag with that name.')

        if tag.creator_id != ctx.author.id:
            if not is_admin(ctx.author):
                return await ctx.send(f'You don\'t have permission to do that.')

        await tag.delete()
        await ctx.send('You have successfully deleted your tag.')
