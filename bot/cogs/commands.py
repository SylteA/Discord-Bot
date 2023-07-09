import inspect
from datetime import datetime

import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.utils import get
from tabulate import tabulate

from bot.models import Model, User
from utils.checks import is_staff
from utils.time import human_timedelta


def to_pages_by_lines(content: str, max_size: int):
    pages = [""]
    i = 0
    for line in content.splitlines(keepends=True):
        if len(pages[i] + line) > max_size:
            i += 1
            pages.append("")
        pages[i] += line
    return pages


def predicate(ctx):
    return is_staff(ctx.author)


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._docs_cache = None

    @commands.command(hidden=True)
    @commands.check(predicate)
    async def post_question(self, ctx):
        if is_staff(ctx.author):
            await ctx.message.delete()
            await ctx.send(
                "```Please post your question, rather than asking for help. "
                "It's much easier and less time consuming.```"
            )

    def get_github_link(self, base_url: str, branch: str, command: str):
        obj = self.bot.get_command(command.replace(".", " "))

        source = obj.callback.__code__
        module = obj.callback.__module__

        lines, firstlineno = inspect.getsourcelines(source)
        location = module.replace(".", "/")
        url = f"{base_url}/blob/{branch}/{location}.py#L" f"{firstlineno}-L{firstlineno + len(lines) - 1}"
        return url

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Get source code for the bot or any command."""
        base_url = "https://github.com/SylteA/Discord-Bot"

        if command is None:
            return await ctx.send(base_url)
        cmd = self.bot.get_command(command)
        if cmd is None:
            return await ctx.send(f"That command does not exist:\n{base_url}")
        elif cmd == self.bot.help_command:
            return await ctx.send(
                base_url + "/blob/master/cogs/_help.py"
            )  # sends the custom help command rather than a malformed link

        try:
            source = inspect.getsource(cmd.callback)
        except AttributeError:
            return await ctx.send(f"That command does not exist:\n{base_url}")

        url = self.get_github_link(base_url=base_url, branch="master", command=command)

        pages = to_pages_by_lines(source, max_size=1900)

        await ctx.send(f"Command {cmd.qualified_name}: {url}")

        for page in pages:
            page = page.replace("`", "`\u200b")
            await ctx.send(f"```py\n{page}```")

    @commands.command(name="website", aliases=["web"])
    async def web_(self, ctx):
        """Get the link to Tims website!"""
        embed = discord.Embed(
            title="Tim's Website",
            description="[Visit the website!](https://techwithtim.net/)",
        )
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def git(self, ctx):
        """Git download link"""
        embed = discord.Embed(
            title="Git Download Link",
            description="[Download GIT Here!](https://git-scm.com/downloads)",
        )
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def twitter(self, ctx):
        """View Tims Twitter"""
        embed = discord.Embed(
            title="Tech With Tim Twitter!",
            description="[View Tim's Twitter!](https://twitter.com/TechWithTimm)",
        )
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(name="instagram", aliases=["insta"])
    async def insta_(self, ctx):
        """View Tims Instagram"""
        embed = discord.Embed(
            title="Tech With Tim Instagram!",
            description="[View Tim's Instagram!](https://instagram.com/tech_with_tim)",
        )
        await ctx.message.delete()
        await ctx.send(embed=embed)

    def members(self):
        members = set(self.bot.get_all_members())
        d = {"online": 0, "idle": 0, "dnd": 0, "offline": 0}
        for member in members:
            d[str(member.status)] += 1
        return d

    @commands.command()
    async def users(self, ctx):
        """Information about users"""
        members = self.members()
        await ctx.send(
            f'```Online: {members["online"]}\n'
            f'Idle: {members["idle"]}\n'
            f'DND: {members["dnd"]}\n'
            f'Offline: {members["offline"]}```'
        )

    @commands.command()
    async def member_count(self, ctx):
        """How many members did you say there were?"""
        await ctx.send(f"```Members: {ctx.guild.member_count}```")

    @commands.command()
    async def top_user(self, ctx):
        """Find out who is the top user in our server!"""
        query = """SELECT * FROM users ORDER BY messages_sent DESC LIMIT 1"""
        top_user = await User.fetchrow(query)

        user = self.bot.get_user(top_user["id"])
        if not isinstance(user, discord.User):
            return await ctx.send(
                f"Could not find the top user, but his ID is {user.id}"
                f'\n And he has `{top_user["messages_sent"]}`` messages'
            )
        await ctx.send(f'Top User: {user} \nMessages: `{top_user["messages_sent"]}`')

    @commands.command()
    async def server_messages(self, ctx):
        """Get the total amount of messages sent in the TWT Server"""
        count = await Model.fetchval("SELECT COUNT(*) FROM messages")
        started_counting = datetime(year=2019, month=11, day=13)
        await ctx.send(
            f"I have read `{count}` messages after "
            f"{human_timedelta(started_counting, suffix=False, brief=True, accuracy=2)}"
        )

    @commands.command(name="messages", aliases=["my_messages"])
    async def messages_(self, ctx, member: commands.MemberConverter = None):
        """How many messages have you sent?"""
        member = member or ctx.author

        user = await User.fetch_user(member.id)
        embed = discord.Embed(color=member.color, description=member.mention)
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="Count", value=str(user.messages_sent))
        embed.add_field(name="Since", value=human_timedelta(user.joined_at, accuracy=2))
        embed.set_footer(text=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["lb"])
    async def scoreboard(self, ctx):
        """Scoreboard over users message count"""
        users = await User.fetch("SELECT * FROM users ORDER BY messages_sent DESC LIMIT 10")

        table = []
        for row in users:
            user = self.bot.get_user(row.id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(row.id)
                except discord.HTTPException:
                    user = row.id

            table.append((str(user), row.messages_sent))

        table = tabulate(
            table,
            headers=(
                "User",
                "Messages",
            ),
            tablefmt="fancy_grid",
        )
        await ctx.send(f">>> ```prolog\n{table}\n```")

    @commands.command("pipsearch", aliases=["pip", "pypi"])
    @commands.cooldown(2, 5, commands.BucketType.user)
    async def pipsearch(
        self,
        ctx,
        term,
        order: lambda string: string.lower() = "relevance",
        amount: lambda x: min(int(x), 10) = 10,
    ):
        """Search pypi.org for packages.
        Specify term, order (relevance, trending, updated)and amount (10 is default)
        you want to show."""
        order = await commands.clean_content().convert(ctx=ctx, argument=order)
        if order not in ("relevance", "trending", "updated"):
            return await ctx.send(f"{order} is not a valid order type.")

        async with ctx.typing():
            order_url = {"relevance": "", "trending": "-zscore", "updated": "-created"}
            search = "https://pypi.org/search?q=" + term.replace(" ", "+") + "&o=" + order_url[order]

            async with self.bot.session.get(
                search.replace(":search:", term).replace(":order:", order_url[order])
            ) as resp:
                text = await resp.read()

            bs = BeautifulSoup(text.decode("utf-8"), "html5lib")
            packages = bs.find_all("a", class_="package-snippet")
            results = int(
                (
                    bs.find(
                        "div",
                        class_="split-layout split-layout--table " "split-layout--wrap-on-tablet",
                    )
                    .find("div")
                    .find("p")
                    .find("strong")
                    .text
                )
                .replace(",", "")
                .replace("+", "")
            )
            if results > 0:
                em = discord.Embed(
                    title=f"Searched {term}",
                    description=f"[Showing {amount}/{results} results.]({search})"
                    if results > amount
                    else f"[Showing {results} results.]({search})",
                )
                i = 0
                em.colour = discord.Colour.green()
                for package in packages[:amount]:
                    href = "https://pypi.org" + package.get("href")
                    title = package.find("h3")
                    name = title.find("span", class_="package-snippet__name").text
                    version = title.find("span", class_="package-snippet__version").text
                    desc = package.find("p").text
                    desc = "Unkown Description" if desc == "" else desc
                    em.add_field(
                        name=f"{name} - {version}",
                        value=f"[`{desc}`]({href})",
                        inline=i,
                    )
                    i = not i
            else:
                em = discord.Embed(
                    title=f"Searched for {term}",
                    description=f"No [results]({search}) found.",
                )
                em.colour = discord.Colour.red()
            await ctx.send(embed=em)

    @commands.command(name="suggest")
    async def suggestion(self, ctx, *, suggestion: str):
        """Make a poll/suggestion"""
        await ctx.message.delete()
        em = discord.Embed(description=suggestion)
        em.set_author(
            name=f"Suggestion by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        msg = await ctx.send(embed=em)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command(name="result", aliases=["show"])
    async def result(self, ctx, msg_link: str):
        """Get result of poll"""
        try:
            channel_id = int(msg_link.split("/")[-2])
            msg_id = int(msg_link.split("/")[-1])
            channel = ctx.guild.get_channel(channel_id)
            message = await channel.fetch_message(msg_id)
            reaction_upvote = get(message.reactions, emoji="👍")
            reaction_downvote = get(message.reactions, emoji="👎")
            if message.author != ctx.bot.user:
                if not message.embeds[0].author.name.startswith("Poll"):
                    return await ctx.send("That message is not a poll!")
            else:
                poll_embed = message.embeds[0]
                embed = discord.Embed(description=f"Suggestion: {poll_embed.description}")
                embed.set_author(name=poll_embed.author.name, icon_url=poll_embed.author.icon_url)
                embed.add_field(name="Upvotes:", value=f"{reaction_upvote.count} 👍")
                embed.add_field(name="Downvotes:", value=f"{reaction_downvote.count} 👎")
                await ctx.send(embed=embed)
        except Exception:
            return await ctx.send("That message is not a poll!")


async def setup(bot):
    await bot.add_cog(Commands(bot))
