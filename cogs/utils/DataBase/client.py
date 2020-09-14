from typing import List
from json import loads
import asyncpg
import asyncio

from .tag import Tag
from .rep import Rep
from .user import User
from .message import Message
from .gconfig import FilterConfig


class DataBase(object):
    def __init__(self, bot, pool, loop=None, timeout: float = 60.0):
        self.bot = bot
        self._pool = pool
        self._loop = loop or asyncio
        self.timeout = timeout
        self._rate_limit = asyncio.Semaphore(value=self._pool._maxsize, loop=self._loop)

    @classmethod
    async def create_pool(cls, bot, uri=None, *, min_connections=10, max_connections=10,
                          timeout=60.0, loop=None, **kwargs):
        pool = await asyncpg.create_pool(uri, min_size=min_connections, max_size=max_connections, **kwargs)
        self = cls(bot=bot, pool=pool, loop=loop, timeout=timeout)
        print('Established DataBase pool with {} - {} connections\n'.format(min_connections, max_connections))
        return self

    async def fetch(self, query, *args):
        async with self._rate_limit:
            async with self._pool.acquire() as con:
                return await con.fetch(query, *args, timeout=self.timeout)

    async def fetchrow(self, query, *args):
        async with self._rate_limit:
            async with self._pool.acquire() as con:
                return await con.fetchrow(query, *args, timeout=self.timeout)

    async def execute(self, query: str, *args):
        async with self._rate_limit:
            async with self._pool.acquire() as con:
                return await con.execute(query, *args, timeout=self.timeout)

    async def get_user(self, user_id: int, get_messages: bool = False, get_reps: bool = False):
        """Not excepting errors here as it would only be good for raising a different error."""
        query = """SELECT * FROM users WHERE id = $1"""
        record = await self.fetchrow(query, user_id)
        if record is None:
            # Post new user.
            user = User(bot=self.bot, id=user_id, messages=[], reps=[])
            await user.post()
            return user

        if get_messages:
            messages = await self.get_messages(user_id)
        else:
            messages = []

        if get_reps:
            reps = await self.get_reps(user_id)
        else:
            reps = []

        return User(bot=self.bot, messages=messages, reps=reps, **record)

    async def get_all_users(self, get_messages: bool = False, get_reps: bool = False):
        records = await self.fetch('SELECT * FROM users')
        users = {int(record["id"]): User(bot=self.bot, messages=[], reps=[], **record) for record in records}

        if get_messages:
            records = await self.fetch('SELECT * FROM messages ORDER BY author_id ASC')
            messages = [Message(bot=self.bot, **record) for record in records]
            for message in messages:
                users[message.author_id].messages.append(message)

        if get_reps:
            records = await self.fetch("SELECT * FROM reps ORDER BY user_id ASC")
            reps = [Rep(bot=self.bot, **record) for record in records]
            for rep in reps:
                users[rep.user_id].reps.append(rep)

        return [x for x in list(users.values())]

    async def get_messages(self, author_id: int) -> List[Message]:
        query = """SELECT * FROM messages WHERE author_id = $1"""
        records = await self.fetch(query, author_id)
        return [Message(bot=self.bot, **record) for record in records]

    async def get_message(self, message_id: int) -> Message:
        query = """SELECT * FROM messages WHERE message_id = $1"""
        record = await self.fetchrow(query, message_id)
        return Message(bot=self.bot, **record)

    async def get_reps(self, id: int, key: str = 'user_id'):
        if key not in ('author_id', 'user_id'):
            raise RuntimeWarning('get_reps `key` can only be `author_id` or `user_id`')
        query = """SELECT * FROM reps WHERE {} = $1""".format(key)
        records = await self.fetch(query, id)
        return [Rep(bot=self.bot, **record) for record in records]

    async def get_config(self, guild_id: int):
        query = """SELECT * FROM gconfigs WHERE guild_id = $1"""
        record = await self.fetchrow(query, guild_id)
        if record is not None:
            return FilterConfig(bot=self.bot, **record)
        config = FilterConfig(bot=self.bot, guild_id=guild_id, blacklist_urls=[], whitelist_channels=[])
        return await config.post()

    async def get_tag(self, guild_id: int, name: str):
        query = """SELECT * FROM tags WHERE guild_id = $1 AND name = $2"""
        record = await self.fetchrow(query, guild_id, name)
        if record is not None:
            return Tag(bot=self.bot, **record)
        return record
