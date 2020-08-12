from discord.ext import commands
import discord


from .utils.DataBase.tag import Tag
from .utils.checks import is_engineer_check, is_admin


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
    async def tag(self, ctx, *, name: lambda inp: inp.lower()):
        """Main tag group."""
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.send('Could not find a tag with that name.\nAttempting to search **' + name + '**')
            return self.search(ctx, '%'+name+'%')

        await ctx.send("{}".format(tag.text))
        await self.bot.db.execute("UPDATE tags SET uses = uses + 1 WHERE guild_id = $1 AND name = $2",
                                  ctx.guild.id, name)

    @tag.command()
    async def info(self, ctx, *, name: lambda inp: inp.lower()):
        """Get information regarding the specified tag."""
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=3.0)
            return await ctx.send('Could not find a tag with that name.', delete_after=3.0)

        author = self.bot.get_user(tag.creator_id)
        author = str(author) if isinstance(author, discord.User) else "(ID: {})".format(tag.creator_id)
        text = "Tag: {name}\n\n```prolog\nCreator: {author}\n   Uses: {uses}\n```"\
            .format(name=name, author=author, uses=tag.uses)
        await ctx.send(text)

    @tag.command()
    @is_engineer_check()
    async def create(self, ctx, name: lambda inp: inp.lower(), *, text: str):
        """Create a new tag."""
        text = await commands.clean_content().convert(ctx=ctx, argument=text)

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=text)
        if tag is not None:
            return await ctx.send('A tag with that name already exists.')

        tag = Tag(bot=self.bot, guild_id=ctx.guild.id,
                  creator_id=ctx.author.id, name=name, text=text)
        await tag.post()
        await ctx.send('You have successfully created your tag.')

    @tag.command()
    @is_engineer_check()
    async def list(self, ctx):
        """List your existing tags."""
        query = """SELECT name FROM tags WHERE guild_id = $1 AND creator_id = $2"""
        records = await self.bot.db.fetch(query, ctx.guild.id, ctx.author.id)
        if not records:
            return await ctx.send('You don\'t have any tags?')
        await ctx.send(f"**{len(records)} tags by you found on this server.**")

        pager = commands.Paginator()

        for record in records:
            pager.add_line(line=record["name"])

        for page in pager.pages:
            await ctx.send(page)

    @tag.command()
    @is_engineer_check()
    async def edit(self, ctx, name: lambda inp: inp.lower(), *, text: str):
        """Edit a tag"""
        text = await commands.clean_content().convert(ctx=ctx, argument=text)

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=3.0)
            return await ctx.send('Could not find a tag with that name.', delete_after=3.0)

        if tag.creator_id != ctx.author.id:
            if not is_admin(ctx.author):
                return await ctx.send(f'You don\'t have permission to do that.')

        await tag.update(text=text)
        await ctx.send('You have successfully edited your tag.')

    @tag.command()
    @is_engineer_check()
    async def delete(self, ctx, *, name: lambda inp: inp.lower()):
        """Delete a tag."""
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=3.0)
            return await ctx.send('Could not find a tag with that name.', delete_after=3.0)

        if tag.creator_id != ctx.author.id:
            if not is_admin(ctx.author):
                return await ctx.send(f'You don\'t have permission to do that.')

        await tag.delete()
        await ctx.send('You have successfully deleted your tag.')
    
    @tag.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def search(self, ctx, *, term: str):
        """Search for a tag given a search term. PostgreSQL syntax must be used for the search."""
        query = """SELECT name FROM tags WHERE guild_id = $1 AND name LIKE $2 LIMIT 10"""
        records = await self.bot.db.fetch(query, ctx.guild.id, term)

        if not records:
            return await ctx.send("No tags found that has the term in it's name")
        elif len(records) == 1:
            await ctx.send(f"Found one tag: **{records[0]['name']}**.")
            return await self.tag(ctx, name=term)
        count = "Maximum of 10" if len(records) == 10 else len(records)
        records = "\n".join([record["name"] for record in records])

        await ctx.send(f"**{count} tags found with search term on this server.**```\n{records}\n```")
