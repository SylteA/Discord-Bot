from discord.ext import commands
import discord

from datetime import datetime, timedelta
import inspect
import pandas
import typing
import zlib
import re
import os
import io

from .utils.DataBase import User

from .youtube import to_pages_by_lines
from .utils.time import human_timedelta
from .utils.checks import is_mod


def finder(text, collection, *, key=None, lazy=True):
    """Credits to github.com/Rapptz"""
    suggestions = []
    text = str(text)
    pat = '.*?'.join(map(re.escape, text))
    regex = re.compile(pat, flags=re.IGNORECASE)
    for item in collection:
        to_search = key(item) if key else item
        r = regex.search(to_search)
        if r:
            suggestions.append((len(r.group()), r.start(), item))

    def sort_key(tup):
        if key:
            return tup[0], tup[1], key(tup[2])
        return tup

    if lazy:
        return (z for _, _, z in sorted(suggestions, key=sort_key))
    else:
        return [z for _, _, z in sorted(suggestions, key=sort_key)]


class SphinxObjectFileReader:
    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode('utf-8')

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(16 * 1024)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b''
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b'\n')
            while pos != -1:
                yield buf[:pos].decode('utf-8')
                buf = buf[pos + 1:]
                pos = buf.find(b'\n')

def parse_object_inv(stream, url):
    result = {}
    inv_version = stream.readline().rstrip()  # version info

    if inv_version != '# Sphinx inventory version 2':
        raise RuntimeError('Invalid objects.inv file version.')
    projname = stream.readline().rstrip()[11:]  # Project name; "# Project: <name>"
    version = stream.readline().rstrip()[11:]  # Version name; "# Version: <version>"

    line = stream.readline()  # says if it's a zlib header
    if 'zlib' not in line:
        raise RuntimeError('Invalid objects.inv file, not z-lib compatible.')

    # This code mostly comes from the Sphinx repository.
    entry_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
    for line in stream.read_compressed_lines():
        match = entry_regex.match(line.rstrip())
        if not match:
            continue

        name, directive, prio, location, dispname = match.groups()
        domain, _, subdirective = directive.partition(':')
        if directive == 'py:module' and name in result:
            # From the Sphinx Repository:
            # due to a bug in 1.1 and below,
            # two inventory entries are created
            # for Python modules, and the first
            # one is correct
            continue

        if directive == 'std:doc':  # Most documentation pages have a label
            subdirective = 'label'

        if location.endswith('$'):
            location = location[:-1] + name

        key = name if dispname == '-' else dispname
        prefix = f'{subdirective}:' if domain == 'std' else ''

        if projname == 'discord.py':
            key = key.replace('discord.ext.commands.', '').replace('discord.', '')

        result[f'{prefix}{key}'] = os.path.join(url, location)

    return result


def predicate(ctx):
    return is_mod(ctx.author)


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._docs_cache = None

    @commands.command(hidden=True)
    @commands.check(predicate)
    async def post_question(self, ctx):
        if is_mod(ctx.author):
            await ctx.message.delete()
            await ctx.send("```Please post your question, rather than asking for help. "
                           "It's much easier and less time consuming.```")

    def get_github_link(self, base_url: str, branch: str, command: str):
        obj = self.bot.get_command(command.replace('.', ' '))

        source = obj.callback.__code__
        module = obj.callback.__module__

        lines, firstlineno = inspect.getsourcelines(source)
        location = module.replace('.', '/')
        url = f'{base_url}/blob/{branch}/{location}.py#L{firstlineno}-L{firstlineno + len(lines) - 1}'
        return url

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Get source code for the bot or any command."""
        base_url = "https://github.com/techwithtim/Discord-Bot"

        if command is None:
            return await ctx.send(base_url)
        cmd = self.bot.get_command(command)
        if cmd is None:
            return await ctx.send(f'That command does not exist:\n{base_url}')

        try:
            source = inspect.getsource(cmd.callback)
        except AttributeError:
            return await ctx.send(f'That command does not exist:\n{base_url}')

        url = self.get_github_link(base_url=base_url, branch='master', command=command)

        pages = to_pages_by_lines(source, max_size=1900)

        if not len(pages) > 1:
            page = pages[0].replace("`", "`\u200b")
            await ctx.send(f'Command {cmd.qualified_name}: {url}'
                           f'\n```py\n{page}```')
        else:
            page = pages[0].replace("`", "`\u200b")
            await ctx.send(f'Command {cmd.qualified_name}: {url}'
                           f'\n```py\n{page}```')
            del pages[0]
            for page in pages:
                page = page.replace("`", "`\u200b")
                await ctx.send(f'```py\n{page}```')

    @commands.command(name='website', aliases=['web'])
    async def web_(self, ctx):
        """Get the link to Tims website!"""
        embed = discord.Embed(title="Tim's Website", description="[Visit the website!](https://techwithtim.net/)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def git(self, ctx):
        """Git download link"""
        embed = discord.Embed(title="Git Download Link",
                              description="[Download GIT Here!](https://git-scm.com/downloads)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def twitter(self, ctx):
        """View Tims Twitter"""
        embed = discord.Embed(title="Tech With Tim Twitter!",
                              description="[View Tim's Twitter!](https://twitter.com/TechWithTimm)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(name='instagram', aliases=['insta'])
    async def insta_(self, ctx):
        """View Tims Instagram"""
        embed = discord.Embed(title="Tech With Tim Instagram!",
                              description="[View Tim's Instagram!](https://instagram.com/tech_with_tim)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    def members(self):
        members = set(self.bot.get_all_members())
        d = {'online': 0, 'idle': 0, 'dnd': 0, 'offline': 0}
        for member in members:
            d[str(member.status)] += 1
        return d

    @commands.command()
    async def users(self, ctx):
        """Information about users"""
        members = self.members()
        await ctx.send(f'```Online: {members["online"]}\n'
                       f'Idle: {members["idle"]}\n'
                       f'DND: {members["dnd"]}\n'
                       f'Offline: {members["offline"]}```')

    @commands.command()
    async def member_count(self, ctx):
        """How many members did you say there were?"""
        await ctx.send(f"```Members: {ctx.guild.member_count}```")

    @commands.command()
    async def top_user(self, ctx):
        """Find out who is the top user in our server!"""
        query = """SELECT * FROM users ORDER BY messages_sent DESC LIMIT 1"""
        top_user = await self.bot.db.fetchrow(query)

        user = self.bot.get_user(top_user['id'])
        if not isinstance(user, discord.User):
            return await ctx.send(f'Could not find the top user, but his ID is {user.id}'
                                  f'\n And he has `{top_user["messages_sent"]}`` messages')
        await ctx.send(f'Top User: {user} \nMessages: `{top_user["messages_sent"]}`')

    @commands.command()
    async def server_messages(self, ctx):
        """Get the total amount of messages sent in the TWT Server"""
        messages = await self.bot.db.fetchrow('SELECT COUNT(*) FROM messages')
        count = messages['count']
        started_counting = datetime(year=2019, month=11, day=13)
        await ctx.send(f"I have read `{count}` messages after "
                       f"{human_timedelta(started_counting, suffix=False, brief=True, accuracy=2)}")

    @commands.command(name='messages', aliases=['my_messages'])
    async def messages_(self, ctx, member: typing.Optional[commands.MemberConverter]):
        """How many messages have you sent?"""
        member = member or ctx.author
        user = await self.bot.db.get_user(member.id)
        await ctx.send(f"Messages: {user.messages_sent}"
                       f"\nSince: {human_timedelta(user.joined_at, brief=True, accuracy=2)}")

    def user__repr__(self, id: int) -> str:
        user = self.bot.get_user(id)
        if isinstance(user, discord.User):
            return str(user)
        return f'(ID: {id})'

    @commands.command()
    async def scoreboard(self, ctx):
        """Scoreboard over users message count"""
        records = await self.bot.db.fetch('SELECT * FROM users ORDER BY messages_sent DESC LIMIT 5')
        users = [User(bot=self.bot, messages=[], reps=[], **record) for record in records]

        users_ = []
        for user in users:
            users_.append((self.user__repr__(user.id), user.messages_sent))

        users_.sort(key=lambda x: x[1], reverse=True)
        users_ = users_[:5]

        frame = pandas.DataFrame(users_, columns=["user", "messages"])
        frame.sort_values(by=['messages'], ascending=False)

        await ctx.send(f'```{frame.head().to_string(index=False)}```')

    @commands.command(name='reps', aliases=['my_reps'])
    async def reps_(self, ctx, member: typing.Optional[commands.MemberConverter]):
        """How many reps do you have?"""
        member = member or ctx.author
        user = await self.bot.db.get_user(member.id, get_reps=True)

        reps = len(user.reps)
        ret = f'{member.display_name} has received `{reps}` reps'
        if reps > 0:
            last_rep = max(user.reps, key=lambda r: r.repped_at)
            ret += f'\nLast rep: {human_timedelta(last_rep.repped_at)}'

        await ctx.send(ret)

    @commands.command()
    async def rep_scoreboard(self, ctx):
        """Rep scoreboard!"""
        users = await self.bot.db.get_all_users(get_reps=True, get_messages=False)

        users_ = []
        for user in users:
            users_.append((self.user__repr__(user.id), len(user.reps)))

        users_.sort(key=lambda x: x[1], reverse=True)
        users_ = users_[:5]

        frame = pandas.DataFrame(users_, columns=["user", "reps"])
        frame.sort_values(by=['reps'], ascending=False)

        await ctx.send(f'```{frame.head().to_string(index=False)}```')

    @commands.command(name='rep')
    async def rep(self, ctx, member: commands.MemberConverter):
        """Rep someone! 24hr cooldown."""
        if member.id == ctx.author.id:
            return await ctx.send('You cannot rep yourself.')

        if member.bot:
            return await ctx.send('You cannot rep bots.')

        user = await self.bot.db.get_user(member.id)

        result = await user.add_rep(message_id=ctx.message.id, author_id=ctx.author.id,
                                    repped_at=ctx.message.created_at, extra_info={"channel_id": ctx.channel.id})

        if result is not None:
            delta = timedelta(days=1, hours=0, minutes=0, seconds=0, milliseconds=0, microseconds=0)
            return await ctx.send(f'{ctx.author.mention} You can rep **{member.display_name}** '
                                  f'again in {human_timedelta(result + delta, suffix=False, accuracy=2)}')
        else:
            await ctx.send(f"{ctx.author.mention} has repped **{member.display_name}**!")

    async def build_docs_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            async with self.bot.session.get(page + '/objects.inv') as resp:
                if resp.status != 200:
                    raise RuntimeError('Cannot build docs lookup table, try again later.')

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = parse_object_inv(stream, page)

        self._docs_cache = cache

    async def get_docs(self, ctx, key, obj):
        page_types = {
            'latest': 'https://discordpy.readthedocs.io/en/latest',
            'python': 'https://docs.python.org/3',
            'pygame': 'https://www.pygame.org/docs'
        }

        if obj is None:
            await ctx.send(page_types[key])
            return

        if self._docs_cache is None:
            await self.build_docs_lookup_table(page_types)

        obj = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)

        if key.startswith('latest'):
            q = obj.lower()  # point the abc.Messageable types properly:
            for name in dir(discord.abc.Messageable):
                if name[0] == '_':
                    continue
                if q == name:
                    obj = f'abc.Messageable.{name}'
                    break

        cache = list(self._docs_cache[key].items())

        matches = finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        if len(matches) == 0:
            return await ctx.send('Could not find anything. Sorry.')

        e = discord.Embed(colour=discord.Colour.blue())

        author = {
            "latest": "discord.py",
            "python": "python",
            "pygame": "pygame"
        }.get(key)

        e.set_author(name=f"{author} docs result", url=page_types.get(key, 'unknown'))
        e.description = '\n'.join(f'[`{key}`]({url})' for key, url in matches)
        await ctx.send(embed=e)

    @commands.group(invoke_without_command=True)
    async def docs(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a discord.py entity.
        Events, objects, and functions are all supported through a
        a cruddy fuzzy algorithm.

        Props to github.com/Rapptz
        """
        if ctx.invoked_subcommand is None:
            await self.get_docs(ctx, 'latest', obj)

    @docs.command(name='python', aliases=['py'])
    async def python_docs(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a Python entity.

        Props to github.com/Rapptz"""
        await self.get_docs(ctx, 'python', obj)

    @docs.command(name='pygame', aliases=['pg'])
    async def pygame_docs(self, ctx, *, obj: str = None):
        """Gives you a documentation link for a PyGame entity.

        Props to github.com/Rapptz"""
        await self.get_docs(ctx, 'pygame', obj)

def setup(bot):
    bot.add_cog(Commands(bot))
