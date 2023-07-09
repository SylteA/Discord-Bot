import asyncio
import logging
from typing import ClassVar, List, Type, TypeVar, Union

from asyncpg import Connection, Pool, Record, connect, create_pool
from pydantic import BaseModel

BM = TypeVar("BM", bound="Model")
log = logging.getLogger(__name__)


class Model(BaseModel):
    pool: ClassVar[Pool] = None

    @classmethod
    async def create_pool(
        cls,
        uri: str,
        *,
        min_con: int = 1,
        max_con: int = 10,
        loop: asyncio.AbstractEventLoop = None,
        **kwargs,
    ) -> None:
        cls.pool = await create_pool(uri, min_size=min_con, max_size=max_con, loop=loop, **kwargs)
        log.info(f"Established a pool with {min_con} - {max_con} connections\n")

    @classmethod
    async def create_connection(cls, uri: str, **kwargs) -> Connection:
        return await connect(uri, **kwargs)

    @classmethod
    async def fetch(
        cls: Type[BM], query, *args, con: Union[Connection, Pool] = None, convert: bool = True
    ) -> Union[List[BM], List[Record]]:
        if con is None:
            con = cls.pool
        records = await con.fetch(query, *args)
        if cls is Model or convert is False:
            return records
        return [cls(**record) for record in records]

    @classmethod
    async def fetchrow(
        cls: Type[BM], query, *args, con: Union[Connection, Pool] = None, convert: bool = True
    ) -> Union[BM, Record, None]:
        if con is None:
            con = cls.pool
        record = await con.fetchrow(query, *args)
        if cls is Model or record is None or convert is False:
            return record
        return cls(**record)

    @classmethod
    async def fetchval(cls, query, *args, con: Union[Connection, Pool] = None, column: int = 0):
        if con is None:
            con = cls.pool
        return await con.fetchval(query, *args, column=column)

    @classmethod
    async def execute(cls, query: str, *args, con: Union[Connection, Pool] = None) -> str:
        if con is None:
            con = cls.pool
        return await con.execute(query, *args)
