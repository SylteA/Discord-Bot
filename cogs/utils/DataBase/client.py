# TODO: Update the commands that use `self.bot.db`


from typing import List
import asyncpg
import asyncio

from .user import User
from .message import Message


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

    async def get_user(self, user_id: int, get_messages: bool = True):
        """Not excepting errors here as it would only be good for raising a different error.
        When using this you want to try: except TimeoutError.
        Timeout is set at `self.timeout`"""
        query = """SELECT * FROM users WHERE id = $1"""
        record = await self.fetchrow(query, user_id)
        if record is None:
            # Post new user.
            user = User(bot=self.bot, id=user_id, messages=[])
            await user.post()
            return user

        if get_messages:
            messages = await self.get_messages(user_id)
            # Temporary solution for getting user messages, still works great though
        else:
            messages = []

        return User(bot=self.bot, messages=messages, **record)

    async def get_messages(self, author_id: int) -> List[Message]:
        query = """SELECT * FROM messages WHERE author_id = $1"""
        records = await self.fetch(query, author_id)
        return [Message(bot=self.bot, **record) for record in records]
