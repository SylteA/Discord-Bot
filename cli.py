import asyncio
import logging
import pathlib
import re
from functools import wraps
from typing import Callable, Dict, Optional, Tuple, TypeVar

import asyncpg
import click
import discord
from aiohttp import ClientSession

from bot.config import settings
from bot.core import DiscordBot
from bot.models import Model
from bot.models.migrations.migration import Migration
from bot.services import http

FN = TypeVar("FN", bound=Callable)

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
MIGRATIONS_PATH = ROOT_DIR / "bot" / "models" / "migrations"

REVISION_FILE = re.compile(r"(?P<version>\d+)_(?P<direction>(up)|(down))__(?P<name>.+).sql")

log = logging.getLogger(__name__)


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
        for file in MIGRATIONS_PATH.glob("*.sql"):
            match = REVISION_FILE.match(file.name)
            if match is not None:
                mig = Migration.from_match(match)
                cls._revisions[mig.version, mig.direction] = mig


async def prepare_postgres(postgres_uri: str, retries: int = 5, interval: float = 5.0, **cp_kwargs) -> bool:
    """
    Prepare the postgres database connection.

    :param str postgres_uri:  The postgresql URI to connect to.
    :param int retries:       Included to fix issue with docker starting API before DB is finished starting.
    :param float interval:    Interval of which to wait for next retry.
    """

    db_log = logging.getLogger("DB")
    db_name = postgres_uri.split("/")[-1]

    if Model.pool is not None:
        db_log.info("No need to create pool, it already exists!")
        return True

    db_log.info(f'Attempting to connect to DB "{db_name}"')
    for i in range(1, retries + 1):
        try:
            await Model.create_pool(uri=postgres_uri, **cp_kwargs)
            break

        except asyncpg.InvalidPasswordError as e:
            db_log.error(str(e))
            return False

        except (ConnectionRefusedError,):
            db_log.warning(f"Failed attempt #{i}/{retries}, trying again in {interval}s")

            if i == retries:
                db_log.error("Failed final connection attempt, exiting.")
                return False

            await asyncio.sleep(interval)

    db_log.info(f'Connected to database "{db_name}"')
    return True


@click.group(invoke_without_command=True)
@click.pass_context
@async_command
async def main(ctx):
    discord.utils.setup_logging()

    if ctx.invoked_subcommand is not None:
        return

    if not await prepare_postgres(
        settings.postgres.uri,
        max_con=settings.postgres.max_pool_connections,
        min_con=settings.postgres.min_pool_connections,
    ):
        exit(1)

    cur = await get_current_db_rev()

    if cur is None:
        latest, _ = max(Revisions.revisions().keys())
        log.info("No migrations have been ran, running all migrations!")
        await update(latest, True)
    else:
        latest, _ = max(Revisions.revisions().keys())

        output = f"Running on migration {str(cur.version).zfill(3)}"
        log.info(output)

        available_migrations = await get_available_migrations()

        if available_migrations:
            log.info("+" + "-" * 35 + "+")
            log.info(f" There are {len(available_migrations)} available Migrations! ")
            for migration in reversed(available_migrations):
                log.info(f" {str(migration.version).zfill(3)}: {migration.name}")
            log.info("+" + "-" * 35 + "+")
            await asyncio.sleep(2)

    prefixes = ("t.",)
    extensions = (
        "jishaku",
        "bot.extensions.adventofcode",
        "bot.extensions.challenges",
        "bot.extensions.github",
        "bot.extensions.levelling",
        "bot.extensions.persistent_roles",
        "bot.extensions.custom_roles",
        "bot.extensions.polls",
        "bot.extensions.readthedocs",
        "bot.extensions.suggestions",
        "bot.extensions.tags",
        "bot.extensions.youtube",
        "bot.cogs.roles",
    )

    intents = discord.Intents.all()

    async with ClientSession() as session:
        http.session = session

        async with DiscordBot(prefixes=prefixes, extensions=extensions, intents=intents) as bot:
            await bot.start(settings.bot.token)


async def run_migration(file: str = "000_up__migrations.sql") -> Migration:
    with open(MIGRATIONS_PATH / file) as f:
        query = f.read()

    match = REVISION_FILE.match(file)
    mig = Migration.from_match(match)

    await Model.execute(query)
    log.info(f"Migration {mig.name} ({file}) was executed.")

    await mig.post()
    return mig


async def get_current_db_rev() -> Optional[Migration]:
    try:
        return await Migration.fetch_latest()
    except asyncpg.UndefinedTableError:
        log.error("Relation 'migrations' does not exits.\nCreating one now...")
        await run_migration()


async def get_available_migrations():
    """Gets info about migrations which have not been executed"""
    curr_migration = await get_current_db_rev()
    available_migrations = []
    for values in Revisions.revisions().values():
        if values.version > curr_migration.version and values.direction == "up":
            available_migrations.append(values)

    return available_migrations


@main.group(invoke_without_command=True)
@click.pass_context
@async_command
async def migrate(ctx):
    """Show the current migrate info"""

    if not await prepare_postgres(settings.postgres.uri):  # Setup db for (sub)commands to use
        return log.error("Failed to prepare Postgres.")

    if ctx.invoked_subcommand is not None:
        return

    rev = await get_current_db_rev()

    if rev is None:
        log.info("No migrations was found. Start one using the `up` command.")
    else:
        log.info("Current Migration:")
        log.info(f"Name      : {rev.name}")
        log.info(f"Version   : {rev.version}")
        log.info(f"Direction : {rev.direction}")
        log.info(f"Latest run: {rev.timestamp}")

    available_migrations = await get_available_migrations()

    if available_migrations:
        for migration in reversed(available_migrations):
            log.info(f"{str(migration.version).zfill(3)}: {migration.name}")


async def update(n: int, is_target: bool = False):
    """
    :param n: amount of steps if `is_target` is False (default), otherwise it is treated as a target version
    :param is_target: whether to treat n as the targeted version or amount of steps
    """

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

    if is_target:
        k = n if n > 0 else -n - 1
        if k == cur.version:
            return log.error("Current migration's version is already equal to targeted version")

        if n > 0 and n > cur.version:
            n = n - cur.version
        elif n < 0 and n < cur.version:
            n = -n - cur.version - 1
        else:
            w = "higher" if n > 0 else "lower"
            return log.error(f"Current migration's version is already {w} than targeted version")

    target = cur.version + n

    if target < 0:
        return log.info("Can't migrate down that far")
    elif target > max(revs.keys())[0]:
        return log.info("Can't migrate up that far")

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
        return log.error("Version can't be less than 1.")

    if direction not in ("up", "down"):
        return log.error("Direction can be either 'up' or 'down'")

    rev = Revisions.revisions().get((version, direction))

    if rev is None:
        return log.error("Migration with that version/direction doesn't exist.")

    await run_migration(rev.filename)


@migrate.command()
@click.argument("n", type=int, required=False)
@click.option("--target", "-t", help="Treats n as a targeted version.", is_flag=True)
@async_command
async def up(n: Optional[int], target):
    """Migrating up. Migrates up all the way if `n` isn't passed (n >= 1)"""
    if n is None:
        n, _ = max(Revisions.revisions().keys())
        target = True
    if n < 1:
        return log.error("Passed argument must be >= 1")
    await update(n, is_target=target)


@migrate.command()
@click.argument("n", type=int, required=False)
@click.option("--confirm", "-c", help="Skips the confirmation message", is_flag=True)
@click.option("--target", "-t", help="Treats n as a targeted version.", is_flag=True)
@async_command
async def down(n: Optional[int], confirm, target):
    """Migrating down. Migrates down all the way if `n` isn't passed (n >= 1)"""
    confirm = confirm or click.confirm("This may result in loss of data, continue?\n")
    if confirm is False:
        return
    if n is None:
        n = 1
        target = True
    if n < 1:
        return log.error("Passed argument must be >= 1")
    await update(-n, is_target=target)


if __name__ == "__main__":
    main()
