import asyncio
from datetime import datetime

import asyncpg
import discord
from config import TAGS_LOG_CHANNEL_ID
from discord.ext import commands

from .utils.checks import is_admin, is_engineer_check, is_staff
from .utils.DataBase.tag import Tag

EMOJIS = [
    "\N{WHITE HEAVY CHECK MARK}",
    "\N{CROSS MARK}",
]


def setup(bot):
    bot.add_cog(TagCommands(bot=bot))


class TagCommands(commands.Cog, name="Tags"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channel = self.bot.get_channel(TAGS_LOG_CHANNEL_ID)

    def cog_check(self, ctx):
        if ctx.guild is None:
            return False

        return True

    def limit_string(self, text: str):
        if len(text) > 1024:
            return text[:1021] + "..."
        return text

    ####################################################################################################################
    # Commands
    ####################################################################################################################

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, name: commands.clean_content):
        """Main tag group."""
        name = name.lower()
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=10.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=10.0)

        await ctx.send("{}".format(tag.text))
        await self.bot.db.execute(
            "UPDATE tags SET uses = uses + 1 WHERE guild_id = $1 AND name = $2",
            ctx.guild.id,
            name,
        )

    @tag.command()
    async def info(self, ctx, *, name: commands.clean_content):
        """Get information regarding the specified tag."""
        name = name.lower()
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=10.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=10.0)

        author = self.bot.get_user(tag.creator_id)
        author = (
            str(author)
            if isinstance(author, discord.User)
            else "(ID: {})".format(tag.creator_id)
        )
        text = (
            "Tag: {name}\n\n```prolog\nCreator: {author}\n   Uses: {uses}\n```".format(
                name=name, author=author, uses=tag.uses
            )
        )
        await ctx.send(text)

    @tag.command()
    @is_engineer_check()
    async def create(
        self, ctx, name: commands.clean_content, *, text: commands.clean_content
    ):
        """Create a new tag."""
        name = name.lower()

        if len(name) > 32:
            return await ctx.send("Tag name must be less than 32 characters.")

        if len(text) > 2000:
            return await ctx.send("Tag text must be less than 2000 characters.")

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)
        if tag is not None:
            return await ctx.send("A tag with that name already exists.")

        if is_staff(ctx.author):
            tag = Tag(
                bot=self.bot,
                guild_id=ctx.guild.id,
                creator_id=ctx.author.id,
                name=name,
                text=text,
            )

            await tag.post()

            await self.log_channel.send(
                embed=discord.Embed(
                    title="Tag Created",
                    description=text,
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
                .add_field(name="Name", value=name)
                .set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
                .set_footer(
                    text=f"Approved By: {ctx.author}", icon_url=ctx.author.avatar_url
                )
            )

            return await ctx.send("You have successfully created your tag.")

        log = await self.log_channel.send(
            embed=discord.Embed(
                title="Tag Create Request",
                description=text,
                timestamp=datetime.utcnow(),
                color=discord.Color.blurple(),
            )
            .add_field(name="Name", value=name)
            .add_field(name="Creator ID", value=ctx.author.id)
            .set_author(name=ctx.author, icon_url=ctx.author.avatar_url),
        )

        for emoji in EMOJIS:
            await log.add_reaction(emoji)

        return await ctx.reply("Tag creation request submitted.")

    @tag.command()
    @is_engineer_check()
    async def list(self, ctx, member: commands.MemberConverter = None):
        """List your existing tags."""
        member = member or ctx.author
        query = """SELECT name FROM tags WHERE guild_id = $1 AND creator_id = $2 ORDER BY name"""
        records = await self.bot.db.fetch(query, ctx.guild.id, member.id)
        if not records:
            return await ctx.send("No tags found.")

        await ctx.send(
            f"**{len(records)} tags by {'you' if member == ctx.author else str(member)} found on this server.**"
        )

        pager = commands.Paginator()

        for record in records:
            pager.add_line(line=record["name"])

        for page in pager.pages:
            await ctx.send(page)

    @tag.command()
    @commands.cooldown(1, 3600 * 24, commands.BucketType.user)
    async def all(self, ctx: commands.Context):
        """List all existing tags alphabetically ordered and sends them in DMs."""
        records = await self.bot.db.fetch(
            """SELECT name FROM tags WHERE guild_id = $1 ORDER BY name""", ctx.guild.id
        )

        if not records:
            return await ctx.send("This server doesn't have any tags.")

        try:
            await ctx.author.send(f"***{len(records)} tags found on this server.***")
        except discord.Forbidden:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Could not dm you...", delete_after=10)

        async def send_tags():
            pager = commands.Paginator()

            for record in records:
                pager.add_line(line=record["name"])

            for page in pager.pages:
                await asyncio.sleep(1)
                await ctx.author.send(page)

        asyncio.create_task(send_tags())

        await ctx.send("Tags are being sent in DMs.")

    @tag.command()
    @is_engineer_check()
    async def edit(
        self, ctx, name: commands.clean_content, *, text: commands.clean_content
    ):
        """Edit a tag"""
        name = name.lower()

        if len(text) > 2000:
            return await ctx.send("Tag text must be less than 2000 characters.")

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=10.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=10.0)

        if tag.creator_id != ctx.author.id:
            if not is_admin(ctx.author):
                return await ctx.send("You don't have permission to do that.")

        if is_staff(ctx.author):
            await tag.update(text=text)

            await self.log_channel.send(
                embed=discord.Embed(
                    title="Tag Updated",
                    color=discord.Color.green(),
                    description=f"**Before**: {tag.text}\n\n**After**: {text}",
                ).set_footer(
                    text=f"Updated By: {ctx.author}", icon_url=ctx.author.avatar_url
                )
            )

            return await ctx.send("You have successfully edited your tag.")

        log = await self.log_channel.send(
            embed=discord.Embed(
                title="Tag Update Request",
                timestamp=datetime.utcnow(),
                color=discord.Color.blurple(),
                description=f"**After**: {text}",
            )
            .add_field(name="Before", value=self.limit_string(tag.text), inline=False)
            .add_field(name="Name", value=name)
            .add_field(name="Creator ID", value=ctx.author.id)
            .set_author(name=ctx.author, icon_url=ctx.author.avatar_url),
        )

        for emoji in EMOJIS:
            await log.add_reaction(emoji)

        return await ctx.reply("Tag update request submitted.")

    @tag.command()
    @is_engineer_check()
    async def delete(self, ctx, *, name: commands.clean_content):
        """Delete a tag."""
        name = name.lower()
        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=10.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=10.0)

        if tag.creator_id != ctx.author.id:
            if not is_staff(ctx.author):
                return await ctx.send("You don't have permission to do that.")

        await tag.delete()
        await ctx.send("You have successfully deleted your tag.")

        author = await self.bot.resolve_user(tag.creator_id)

        await self.log_channel.send(
            embed=discord.Embed(
                title="Tag Deleted",
                description=tag.text,
                color=discord.Color.red(),
                timestamp=datetime.utcnow(),
            )
            .add_field(name="Name", value=name)
            .set_author(name=author, icon_url=author.avatar_url)
            .set_footer(
                text=f"Deleted By: {ctx.author}", icon_url=ctx.author.avatar_url
            )
        )

    @tag.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def search(self, ctx, *, term: str):
        """Search for a tag given a search term. PostgreSQL syntax must be used for the search."""
        query = (
            """SELECT name FROM tags WHERE guild_id = $1 AND name LIKE $2 LIMIT 10"""
        )
        records = await self.bot.db.fetch(query, ctx.guild.id, term)

        if not records:
            return await ctx.send(
                "No tags found that has the term in it's name", delete_after=10
            )
        count = "Maximum of 10" if len(records) == 10 else len(records)
        records = "\n".join([record["name"] for record in records])

        await ctx.send(
            f"**{count} tags found with search term on this server.**```\n{records}\n```"
        )

    @tag.command()
    @is_engineer_check()
    async def rename(
        self, ctx, name: commands.clean_content, *, new_name: commands.clean_content
    ):
        """Rename a tag."""
        name = name.lower()
        new_name = new_name.lower()

        if len(new_name) > 32:
            return await ctx.send("Tag name must be less than 32 characters.")

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=10.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=10.0)

        if tag.creator_id != ctx.author.id:
            if not is_admin(ctx.author):
                return await ctx.send("You don't have permission to do that.")

        try:
            await tag.rename(new_name=new_name)
        except asyncpg.UniqueViolationError:
            return await ctx.send("A tag with that name already exists.")

        await ctx.send("You have successfully renamed your tag.")

    @tag.command()
    @is_engineer_check()
    async def append(
        self, ctx, name: commands.clean_content, *, text: commands.clean_content
    ):
        """Append some content to the end of a tag"""
        name = name.lower()

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)

        if tag is None:
            await ctx.message.delete(delay=10.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=10.0)

        if tag.creator_id != ctx.author.id:
            if not is_admin(ctx.author):
                return await ctx.send("You don't have permission to do that.")

        new_txt = tag.text + " " + text

        if len(new_txt) > 2000:
            return await ctx.send(
                "Cannot append, content length will exceed discords maximum message length."
            )

        if is_staff(ctx.author):
            await tag.update(text=new_txt)
            await self.log_channel.send(
                embed=discord.Embed(
                    title="Tag Updated",
                    color=discord.Color.green(),
                    description=f"**Before**: {tag.text}\n\n**After**: {text}",
                ).set_footer(
                    text=f"Updated By: {ctx.author}", icon_url=ctx.author.avatar_url
                )
            )
            return await ctx.send("You have successfully appended to your tag content.")

        log = await self.log_channel.send(
            embed=discord.Embed(
                title="Tag Update Request",
                timestamp=datetime.utcnow(),
                color=discord.Color.blurple(),
                description=f"**After**: {new_txt}",
            )
            .add_field(name="Before", value=self.limit_string(tag.text), inline=False)
            .add_field(name="Name", value=name)
            .add_field(name="Creator ID", value=ctx.author.id)
            .set_author(name=ctx.author, icon_url=ctx.author.avatar_url),
        )

        for emoji in EMOJIS:
            await log.add_reaction(emoji)

        return await ctx.reply("Tag update request submitted.")

    ####################################################################################################################
    # Listeners
    ####################################################################################################################

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        if event.channel_id != TAGS_LOG_CHANNEL_ID:
            return

        if event.member.bot:
            return

        message = await self.bot.get_channel(event.channel_id).fetch_message(
            event.message_id
        )

        if not message.embeds:
            return

        if str(event.emoji) not in EMOJIS:
            return

        approved = True

        if str(event.emoji) != "\N{WHITE HEAVY CHECK MARK}":
            approved = False

        if message.embeds[0].title == "Tag Create Request":
            return self.bot.dispatch(
                "tag_create_response",
                message,
                approved,
                user=event.member,
            )
        elif message.embeds[0].title == "Tag Update Request":
            return self.bot.dispatch(
                "tag_update_response",
                message,
                approved,
                user=event.member,
            )

    @commands.Cog.listener()
    async def on_tag_create_response(self, message: discord.Message, approved, user):
        text = message.embeds[0].description
        name = message.embeds[0].fields[0].value
        creator_id = int(message.embeds[0].fields[1].value)

        if approved:
            tag = Tag(
                bot=self.bot,
                guild_id=message.guild.id,
                creator_id=creator_id,
                name=name,
                text=text,
            )

            await tag.post()

            author = await self.bot.resolve_user(creator_id)

            return await message.edit(
                embed=discord.Embed(
                    title="Tag Created",
                    description=text,
                    timestamp=datetime.utcnow(),
                    color=discord.Color.green(),
                )
                .add_field(name="Name", value=name)
                .set_author(name=author, icon_url=author.avatar_url)
                .set_footer(text=f"Approved By: {user}", icon_url=user.avatar_url)
            )

        await message.edit(
            embed=discord.Embed(
                title="Tag Creation Denied",
                description=text,
                timestamp=datetime.utcnow(),
                color=discord.Color.red(),
            )
            .add_field(name="Name", value=name)
            .set_author(name=user, icon_url=user.avatar_url)
            .set_footer(text=f"Denied By: {user}", icon_url=user.avatar_url)
        )

    @commands.Cog.listener()
    async def on_tag_update_response(self, message: discord.Message, approved, user):
        text = message.embeds[0].description[11:]
        name = message.embeds[0].fields[1].value
        creator_id = int(message.embeds[0].fields[2].value)
        before = message.embeds[0].fields[0].value

        if approved:
            tag = await self.bot.db.get_tag(guild_id=message.guild.id, name=name)
            author = await self.bot.resolve_user(creator_id)

            if tag is None:
                return await message.edit(
                    embed=discord.Embed(
                        title="Tag Update Failed",
                        description="Tag has been deleted",
                        timestamp=datetime.utcnow(),
                        color=discord.Color.red(),
                    )
                    .add_field(name="Name", value=name)
                    .set_author(name=author, icon_url=author.avatar_url)
                )

            await tag.update(text=text)
            return await message.edit(
                embed=discord.Embed(
                    title="Tag Updated",
                    description=f"**Before**: {before}\n\n**After**: {text}",
                    timestamp=datetime.utcnow(),
                    color=discord.Color.green(),
                )
                .add_field(name="Name", value=name)
                .set_author(name=author, icon_url=author.avatar_url)
                .set_footer(text=f"Approved By: {user}", icon_url=user.avatar_url)
            )

        await message.edit(
            embed=discord.Embed(
                title="Tag Update Denied",
                description=f"**Before**: {before}\n\n**After**: {text}",
                timestamp=datetime.utcnow(),
                color=discord.Color.red(),
            )
            .add_field(name="Name", value=name)
            .set_author(name=user, icon_url=user.avatar_url)
            .set_footer(text=f"Denied By: {user}", icon_url=user.avatar_url)
        )
