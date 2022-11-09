import asyncio
import logging
import pathlib
import re
from functools import wraps
from typing import Callable, Dict, Optional, Tuple, TypeVar

import asyncpg
import click
import discord

from bot import Tim
from cogs.utils.models import Model
from config import settings
from migrations.migration import Migration

FN = TypeVar("FN", bound=Callable)
REVISION_FILE = re.compile(r"(?P<version>\d+)_(?P<direction>(up)|(down))__(?P<name>.+).sql")


def _async(func: FN) -> FN:
    loop = asyncio.get_event_loop()

    @wraps(func)
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(func(*args, **kwargs))

    return wrapper


def get_revisions() -> Tuple[Dict[Tuple[int, str], Migration], int]:
    root = pathlib.Path("migrations")
    revisions = {}
    for file in root.glob("*.sql"):
        match = REVISION_FILE.match(file.name)
        if match is not None:
            mig = Migration.from_match(match)
            revisions[mig.version, mig.direction] = mig
    s, k = {}, 0
    for k in sorted(revisions.keys()):
        s[k] = revisions[k]
    return s, k


async def create_pool():
    log = logging.getLogger()
    try:
        await Model.create_pool()
    except Exception as e:
        return log.exception("Could not set up PostgreSQL.", exc_info=e)  # None


@click.group(invoke_without_command=True)
@click.pass_context
@_async
async def main(ctx):
    if ctx.invoked_subcommand is None:
        discord.utils.setup_logging()
        await create_pool()
        await Tim().start(settings.bot.token)


async def run_migration(file: str = "000_migrations.sql") -> None:
    path = pathlib.Path("migrations")

    with open(path / file) as f:
        query = f.read()

    await Model.execute(query)
    match = REVISION_FILE.match(file)

    if match is None:
        mig = Migration.from_match(match)
        await mig.post()

    click.echo(f"{file} was executed.")


async def get_current_db_rev() -> Optional[Migration]:
    try:
        return await Migration.fetch_latest()
    except asyncpg.UndefinedTableError:
        click.echo("Relation 'migrations' does not exits.\nCreating one now...")
        await run_migration()


@main.group(invoke_without_command=True)
@click.pass_context
@_async
async def migrate(ctx):
    """Show the current migrate info"""

    await create_pool()  # Setup db for (sub)commands to use

    if ctx.invoked_subcommand is not None:
        return

    rev = await get_current_db_rev()

    if rev is None:
        click.echo("No migrations was found. Start one using the `up` command.")
    else:
        click.echo(
            f"Name      : {rev.name}\n"
            f"Version   : {rev.version}\n"
            f"Direction : {rev.direction}\n"
            f"Latest run: {rev.timestamp}"
        )


async def update(n: int):
    """n > 0: upgrading ;; n < 0: downgrading"""

    fake0 = Migration(version=0, direction="up", name="")
    cur = await get_current_db_rev()

    if cur is None:
        cur = fake0

    revs, (k, _) = get_revisions()

    if cur.direction == "down":
        if cur.version == 1:
            cur = fake0
        else:
            cur = revs[cur.version - 1, "up"]

    target = cur.version + n

    if target < 0:
        return click.echo("Can't migrate down that much")
    elif target > k:
        return click.echo("Can't migrate up that much")

    while cur.version != target:
        if cur.version < target:
            cur = revs[cur.version + 1, "up"]
            await run_migration(cur.filename)
        else:
            await run_migration(revs[cur.version, "down"].filename)
            cur = revs.get((cur.version - 1, "up"), fake0)


@migrate.command()
@_async
async def init():
    """Executes the initial migration."""
    await run_migration()


@migrate.command()
@click.argument("version", type=int)
@click.argument("direction", type=str, default="up")
@_async
async def run(version: int, direction: str):
    """Executes a specific migration."""
    if version < 1:
        return click.echo("Version can't be less than 1.")

    if direction not in ("up", "down"):
        return click.echo("Direction can be either 'up' or 'down'")

    revs, _ = get_revisions()
    rev = revs.get((version, direction))

    if rev is None:
        return click.echo("Migration with that version/direction doesn't exist.")

    await run_migration(rev.filename)


@migrate.command()
@click.argument("n", type=int, default=1)
@_async
async def up(n: int):
    """Migrating up n times. (n >= 1 ;; n = 1 by default)"""
    if n < 1:
        return click.echo("Passed integer mast be >= 1")
    await update(n)


@migrate.command()
@click.argument("n", type=int, default=1)
@_async
async def down(n: int):
    """Migrating down n times. (n >= 1 ;; n = 1 by default)"""
    if n < 1:
        return click.echo("Passed integer mast be >= 1")
    await update(-n)


if __name__ == "__main__":
    main()
