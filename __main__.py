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
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
REVISION_FILE = re.compile(r"(?P<version>\d+)_(?P<direction>(up)|(down))__(?P<name>.+).sql")


def async_command(func: FN) -> FN:
    loop = asyncio.get_event_loop()

    @wraps(func)
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(func(*args, **kwargs))

    return wrapper


class Revisions:
    _revisions = {}

    @classmethod
    def revisions(cls) -> Dict[Tuple[int, str], Migration]:
        if not cls._revisions:
            cls.load_revisions()
        return cls._revisions

    @classmethod
    def load_revisions(cls) -> None:
        root = ROOT_DIR / "migrations"
        for file in root.glob("*.sql"):
            match = REVISION_FILE.match(file.name)
            if match is not None:
                mig = Migration.from_match(match)
                cls._revisions[mig.version, mig.direction] = mig


async def create_pool():
    log = logging.getLogger()
    try:
        await Model.create_pool()
    except Exception as e:
        return log.exception("Could not set up PostgreSQL.", exc_info=e)  # None


@click.group(invoke_without_command=True)
@click.pass_context
@async_command
async def main(ctx):
    if ctx.invoked_subcommand is None:
        discord.utils.setup_logging()
        await create_pool()
        await Tim().start(settings.bot.token)


async def run_migration(file: str = "000_migrations.sql") -> None:
    path = ROOT_DIR / "migrations"

    with open(path / file) as f:
        query = f.read()

    await Model.execute(query)
    match = REVISION_FILE.match(file)

    if match is not None:
        mig = Migration.from_match(match)
        await mig.post()

    click.echo(f"{file} was executed.")


async def get_current_db_rev() -> Optional[Migration]:
    try:
        return await Migration.fetch_latest()
    except asyncpg.UndefinedTableError:
        click.echo("Relation 'migrations' does not exits.\nCreating one now...", err=True)
        await run_migration()


@main.group(invoke_without_command=True)
@click.pass_context
@async_command
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


async def update(steps: int):
    """steps > 0: upgrading ;; steps < 0: downgrading"""

    fake0 = Migration(version=0, direction="up", name="")
    cur = await get_current_db_rev()

    if cur is None:
        cur = fake0

    revs = Revisions.revisions()

    if cur.direction == "down":
        if cur.version == 1:
            cur = fake0
        else:
            cur = revs[cur.version - 1, "up"]

    target = cur.version + steps

    if target < 0:
        return click.echo("Can't migrate down that far")
    elif target > max(revs.keys())[0]:
        return click.echo("Can't migrate up that far")

    while cur.version != target:
        if cur.version < target:
            cur = revs[cur.version + 1, "up"]
            await run_migration(cur.filename)
        else:
            await run_migration(revs[cur.version, "down"].filename)
            cur = revs.get((cur.version - 1, "up"), fake0)


@migrate.command()
@async_command
async def init():
    """Executes the initial migration. Creating a `migrations` table."""
    await run_migration()


@migrate.command()
@click.argument("version", type=int)
@click.argument("direction", type=str)
@async_command
async def run(version: int, direction: str):
    """Executes a specific migration."""
    if version < 1:
        return click.echo("Version can't be less than 1.", err=True)

    if direction not in ("up", "down"):
        return click.echo("Direction can be either 'up' or 'down'", err=True)

    rev = Revisions.revisions().get((version, direction))

    if rev is None:
        return click.echo("Migration with that version/direction doesn't exist.", err=True)

    await run_migration(rev.filename)


@migrate.command()
@click.argument("steps", type=int, required=False)
@async_command
async def up(steps: Optional[int]):
    """Migrating up. Migrates up all the way if `steps` isn't passed (steps >= 1)"""
    if steps is None:
        steps, _ = max(Revisions.revisions().keys())
    if steps < 1:
        return click.echo("`steps` must be >= 1", err=True)
    await update(steps)


@migrate.command()
@click.option("--confirm", "-c", help="Skips the confirmation message", is_flag=True)
@click.argument("steps", type=int, required=False)
@async_command
async def down(steps: Optional[int], confirm):
    """Migrating down. Migrates down all the way if `steps` isn't passed (steps >= 1)"""
    confirm = confirm or click.confirm("This may drop postgresql tables, continue?")
    if confirm is False:
        return
    if steps is None:
        steps, _ = max(Revisions.revisions().keys())
    if steps < 1:
        return click.echo("`steps` must be >= 1", err=True)
    await update(-steps)


if __name__ == "__main__":
    main()
