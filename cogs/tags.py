import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, List, Literal

import discord
from discord.ext import commands

from config import TAGS_LOG_CHANNEL_ID, TAGS_REQUESTS_WEBHOOK

from .utils.checks import is_admin, is_engineer_check, is_staff
from .utils.DataBase.tag import Tag

if TYPE_CHECKING:
    from main import Tim

EMOJIS = [
    "\N{WHITE HEAVY CHECK MARK}",
    "\N{CROSS MARK}",
]


def setup(bot):
    bot.add_cog(TagCommands(bot=bot))


class TagCommands(commands.Cog, name="Tags"):
    def __init__(self, bot: "Tim"):
        self.bot = bot
        self.log_channel = self.bot.get_channel(TAGS_LOG_CHANNEL_ID)
        self.webhook = discord.Webhook.from_url(
            TAGS_REQUESTS_WEBHOOK,
            adapter=discord.AsyncWebhookAdapter(self.bot.session),
        )

    def cog_check(self, ctx):
        if ctx.guild is None:
            return False

        return True

    @staticmethod
    def log_embeds(
        rtype: Literal["Create", "Delete", "Update", "Rename"],
        tname: str,
        before: str,
        after: str,
        author_id: int,
        approve: bool = None,
        approver: discord.Member = None,
    ) -> List[discord.Embed]:
        if approve is None:
            color = discord.Color.blurple()
        else:
            color = discord.Color.green() if approve and rtype != "Delete" else discord.Color.red()

        fel = {None: " Request", False: " Denied", True: "d"}
        embeds = [discord.Embed(title=f"Tag {rtype}{fel[approve]}", color=color)]

        if rtype in ("Create", "Delete"):
            embeds[0].description = f"```Content```\n{after}"
        elif rtype == "Update":
            embeds[0].description = f"```Before```\n{before}"
            embeds.append(discord.Embed(description=f"```After```\n{after}", color=color))
        else:  # rtype = "Rename"
            embeds[0].add_field(name="Before", value=before).add_field(name="After", value=after)

        embeds[-1].timestamp = datetime.utcnow()

        if rtype != "Rename":
            embeds[-1].add_field(name="Tag's name", value=tname)

        embeds[-1].add_field(
            name="Author",
            value=f"<@{author_id}> ({author_id})",
            inline=rtype != "Rename",
        )

        if approve is not None:
            if rtype == "Delete":
                action = "Deleted"
            else:
                action = "Approved" if approve else "Denied"
            embeds[-1].set_footer(text=f"{action} by: {approver}")

        return embeds

    @staticmethod
    async def notify(user, text):
        try:
            return await user.send(text)
        except discord.Forbidden:
            pass

    async def request(self, **kwargs):
        embeds = self.log_embeds(**kwargs)
        log: discord.WebhookMessage = await self.webhook.send(embeds=embeds, wait=True)
        log = await self.log_channel.fetch_message(log.id)  # PartialWebhookState does not support http methods

        for emoji in EMOJIS:
            await log.add_reaction(emoji)

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

        await ctx.send(tag.text)
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
        author = str(author) if isinstance(author, discord.User) else f"(ID: {tag.creator_id})"
        text = f"Tag: {name}\n\n```prolog\nCreator: {author}\n   Uses: {tag.uses}\n```"
        await ctx.send(text)

    @tag.command()
    @is_engineer_check()
    async def create(self, ctx, name: commands.clean_content, *, text: commands.clean_content):
        """Create a new tag."""
        name = name.lower()

        if len(name) > 32:
            return await ctx.send("Tag name must be less than 32 characters.")

        if len(text) > 2000:
            return await ctx.send("Tag text must be less than 2000 characters.")

        tag = await self.bot.db.get_tag(guild_id=ctx.guild.id, name=name)
        if tag is not None:
            return await ctx.send("A tag with that name already exists.")

        kwargs = dict(rtype="Create", tname=name, before="", after=text, author_id=ctx.author.id)

        if is_staff(ctx.author):
            tag = Tag(
                bot=self.bot,
                guild_id=ctx.guild.id,
                creator_id=ctx.author.id,
                name=name,
                text=text,
            )
            await tag.post()
            await self.webhook.send(embeds=self.log_embeds(**kwargs, approve=True, approver=ctx.author))

            return await ctx.send("You have successfully created your tag.")

        await self.request(**kwargs)
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
        records = await self.bot.db.fetch("""SELECT name FROM tags WHERE guild_id = $1 ORDER BY name""", ctx.guild.id)

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
    async def edit(self, ctx, name: commands.clean_content, *, text: commands.clean_content):
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

        kwargs = dict(
            rtype="Update",
            tname=name,
            before=tag.text,
            after=text,
            author_id=tag.creator_id,
        )
        if is_staff(ctx.author):
            await tag.update(text=text)
            await self.webhook.send(embeds=self.log_embeds(**kwargs, approve=True, approver=ctx.author))
            return await ctx.send("You have successfully edited your tag.")

        await self.request(**kwargs)
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

        await self.webhook.send(
            embeds=self.log_embeds(
                approve=True,
                rtype="Delete",
                tname=name,
                before="",
                after=tag.text,
                author_id=tag.creator_id,
                approver=ctx.author,
            )
        )

    @tag.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def search(self, ctx, *, term: str):
        """Search for a tag given a search term. PostgreSQL syntax must be used for the search."""
        query = """SELECT name FROM tags WHERE guild_id = $1 AND name LIKE $2 LIMIT 10"""
        records = await self.bot.db.fetch(query, ctx.guild.id, term)

        if not records:
            return await ctx.send("No tags found that has the term in it's name", delete_after=10)
        count = "Maximum of 10" if len(records) == 10 else len(records)
        records = "\n".join([record["name"] for record in records])

        await ctx.send(f"**{count} tags found with search term on this server.**```\n{records}\n```")

    @tag.command()
    @is_engineer_check()
    async def rename(self, ctx, name: commands.clean_content, *, new_name: commands.clean_content):
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

        if await self.bot.db.get_tag(guild_id=ctx.guild.id, name=new_name):
            return await ctx.send("A tag with that name already exists.")

        kwargs = dict(
            rtype="Rename",
            tname="",
            before=name,
            after=new_name,
            author_id=tag.creator_id,
        )
        if is_staff(ctx.author):
            await tag.rename(new_name=new_name)

            await self.webhook.send(embeds=self.log_embeds(**kwargs, approve=True, approver=ctx.author))
            return await ctx.send("You have successfully renamed your tag.")

        await self.request(**kwargs)
        return await ctx.reply("Tag update request submitted.")

    @tag.command()
    @is_engineer_check()
    async def append(self, ctx, name: commands.clean_content, *, text: commands.clean_content):
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

        new_text = tag.text + " " + text

        if len(new_text) > 2000:
            return await ctx.send("Cannot append, content length will exceed discords maximum message length.")

        kwargs = dict(
            rtype="Update",
            tname=name,
            before=tag.text,
            after=new_text,
            author_id=tag.creator_id,
        )
        if is_staff(ctx.author):
            await tag.update(text=new_text)
            await self.webhook.send(embeds=self.log_embeds(**kwargs, approve=True, approver=ctx.author))
            return await ctx.send("You have successfully appended to your tag content.")

        await self.request(**kwargs)
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

        message = await self.bot.get_channel(event.channel_id).fetch_message(event.message_id)

        if not message.embeds:
            return

        if str(event.emoji) not in EMOJIS:
            return

        approved = str(event.emoji) == "\N{WHITE HEAVY CHECK MARK}"

        if message.embeds[0].title == "Tag Create Request":
            await message.clear_reactions()
            return self.bot.dispatch(
                "tag_create_response",
                message,
                approved,
                user=event.member,
            )
        elif message.embeds[0].title == "Tag Update Request":
            await message.clear_reactions()
            return self.bot.dispatch(
                "tag_update_response",
                message,
                approved,
                user=event.member,
            )
        elif message.embeds[0].title == "Tag Rename Request":
            await message.clear_reactions()
            return self.bot.dispatch(
                "tag_rename_response",
                message,
                approved,
                user=event.member,
            )

    @commands.Cog.listener()
    async def on_tag_rename_response(self, message: discord.Message, approved, user):
        embed = message.embeds[0]
        before, after = embed.fields[0].value, embed.fields[1].value
        creator_id = int(embed.fields[-1].value.split("(")[-1][:-1])
        author = await self.bot.resolve_user(creator_id)
        if approved:
            tag = await self.bot.db.get_tag(guild_id=message.guild.id, name=before)

            if tag is None:
                # embed.title = "Tag Rename Failed"
                # embed.colour = discord.Color.red()
                # return await self.webhook.edit_message(message.id, embed=embed)
                return await message.delete()

            await tag.rename(new_name=after)

        await self.webhook.edit_message(
            message.id,
            embeds=self.log_embeds(
                rtype="Rename",
                tname="",
                before=before,
                after=after,
                author_id=author.id,
                approver=user,
                approve=approved,
            ),
        )
        await self.notify(
            author,
            f"Tag `{before}` renaming to `{after}` request has been {['deni', 'approv'][approved]}ed.",
        )

    @commands.Cog.listener()
    async def on_tag_create_response(self, message: discord.Message, approved, user):
        embed = message.embeds[0]
        name, text = embed.fields[0].value, embed.description.split("\n", 1)[-1]
        creator_id = int(embed.fields[-1].value.split("(")[-1][:-1])
        author = await self.bot.resolve_user(creator_id)

        if approved:
            tag = Tag(
                bot=self.bot,
                guild_id=message.guild.id,
                creator_id=creator_id,
                name=name,
                text=text,
            )
            if await self.bot.db.get_tag(guild_id=message.guild.id, name=name):
                # embed.title = "Tag Create Failed"
                # embed.colour = discord.Color.red()
                # return await self.webhook.edit_message(message.id, embed=embed)
                return await message.delete()

            await tag.post()

        await self.webhook.edit_message(
            message.id,
            embeds=self.log_embeds(
                rtype="Create",
                tname=name,
                before="",
                after=text,
                author_id=author.id,
                approver=user,
                approve=approved,
            ),
        )
        await self.notify(
            author,
            f"Tag `{name}` creating request has been {['deni', 'approv'][approved]}ed.",
        )

    @commands.Cog.listener()
    async def on_tag_update_response(self, message: discord.Message, approved, user):
        embeds = message.embeds
        name = embeds[1].fields[0].value
        before, after = (
            embeds[0].description.split("\n", 1)[-1],
            embeds[1].description.split("\n", 1)[-1],
        )
        creator_id = int(embeds[1].fields[-1].value.split("(")[-1][:-1])
        author = await self.bot.resolve_user(creator_id)

        if approved:
            tag = await self.bot.db.get_tag(guild_id=message.guild.id, name=name)

            if tag is None:
                # embeds[0].title = "Tag Update Failed"
                # embeds[0].colour = embeds[1].colour = discord.Color.red()
                # return await self.webhook.edit_message(message.id, embeds=embeds)
                return await message.delete()

            await tag.update(text=after)

        await self.webhook.edit_message(
            message.id,
            embeds=self.log_embeds(
                rtype="Update",
                tname=name,
                before=before,
                after=after,
                author_id=author.id,
                approver=user,
                approve=approved,
            ),
        )
        await self.notify(
            author,
            f"Tag `{name}` updating request has been {['deni', 'approv'][approved]}ed.",
        )
