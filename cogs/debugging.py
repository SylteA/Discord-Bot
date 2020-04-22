import sys

import discord
import humanize
from discord.ext import commands

from jishaku.cog_base import JishakuBase
from jishaku.flags import JISHAKU_HIDE
from jishaku.meta import __version__
from jishaku.metacog import GroupCogMeta
from jishaku.modules import package_version

from jishaku.paginators import PaginatorInterface, WrappedPaginator
from jishaku.exception_handling import ReplResponseReactor
from jishaku.shell import ShellReader

try:
    import psutil
except ImportError:
    psutil = None


@commands.group(name="jishaku", aliases=["jsk", "sudo"], hidden=JISHAKU_HIDE,
                invoke_without_command=True, ignore_extra=False)
async def jsk(self, ctx: commands.Context):
    """
    The Jishaku debug and diagnostic commands.

    This command on its own gives a status brief.
    All other functionality is within its subcommands.
    """

    summary = [
        f"Jishaku v{__version__}, discord.py `{package_version('discord.py')}`, "
        f"`Python {sys.version}` on `{sys.platform}`".replace("\n", ""),
        f"Module was loaded {humanize.naturaltime(self.load_time)}, "
        f"cog was loaded {humanize.naturaltime(self.start_time)}.",
        ""
    ]

    if psutil:
        proc = psutil.Process()

        with proc.oneshot():
            mem = proc.memory_full_info()
            summary.append(f"Using {humanize.naturalsize(mem.rss)} physical memory and "
                           f"{humanize.naturalsize(mem.vms)} virtual memory, "
                           f"{humanize.naturalsize(mem.uss)} of which unique to this process.")

            name = proc.name()
            pid = proc.pid
            thread_count = proc.num_threads()

            summary.append(f"Running on PID {pid} (`{name}`) with {thread_count} thread(s).")

            summary.append("")  # blank line

    cache_summary = f"{len(self.bot.guilds)} guild(s) and {len(self.bot.users)} user(s)"

    if isinstance(self.bot, discord.AutoShardedClient):
        summary.append(f"This bot is automatically sharded and can see {cache_summary}.")
    elif self.bot.shard_count:
        summary.append(f"This bot is manually sharded and can see {cache_summary}.")
    else:
        summary.append(f"This bot is not sharded and can see {cache_summary}.")

    summary.append(f"Average websocket latency: {round(self.bot.latency * 1000, 2)}ms")

    await ctx.send("\n".join(summary))


class Jsk(JishakuBase, metaclass=GroupCogMeta, command_parent=jsk, command_attrs=dict(hidden=True)):
    async def cog_check(self, ctx):
        """Not everyone needs access to this"""
        if ctx.author.id not in (144112966176997376, 501089409379205161):
            return False
        return True

    async def git(self, ctx, pull_push, *, message=None):
        """
        Executes git statements in the system shell.
        This uses the system shell as defined in $SHELL, or `/bin/bash` otherwise.
        Execution can be cancelled by closing the paginator.
        """
        message = message if message is not None else "Updated files."

        if pull_push == "push":
            shellcmd = f'sudo git add .&&sudo git commit -m "{message}"&&sudo git push'
        elif pull_push == "pull":
            shellcmd = 'sudo git pull'
        else:
            return await ctx.send("Invalid option given")

        async with ReplResponseReactor(ctx.message):
            paginator = WrappedPaginator(prefix="```sh", max_size=1985)
            paginator.add_line(f"$ git {pull_push}\n")

            interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
            self.bot.loop.create_task(interface.send_to(ctx))

            with ShellReader(shellcmd) as reader:
                async for line in reader:
                    if interface.closed:
                        return
                    await interface.add_line(line)


def setup(bot):
    bot.add_cog(Jsk(bot))
