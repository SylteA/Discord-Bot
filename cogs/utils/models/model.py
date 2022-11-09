import asyncio
import logging
from typing import ClassVar, List, Type, TypeVar, Union

from asyncpg import Connection, Pool, Record, connect, create_pool
from pydantic import BaseModel

from config import settings

BM = TypeVar("BM", bound="Model")
log = logging.getLogger(__name__)


class Model(BaseModel):
    pool: ClassVar[Pool]

    @classmethod
    async def create_pool(
        cls,
        uri: str = settings.postgres.uri,
        *,
        min_con: int = settings.postgres.min_pool_connections,
        max_con: int = settings.postgres.max_pool_connections,
        loop: asyncio.AbstractEventLoop = None,
        **kwargs,
    ) -> None:
        cls.pool = await create_pool(uri, min_size=min_con, max_size=max_con, loop=loop, **kwargs)
        log.info(f"Established a pool with {min_con} - {max_con} connections\n")

    @classmethod
    async def create_connection(cls, uri: str = settings.postgres.uri, **kwargs) -> Connection:
        return await connect(uri, **kwargs)

    @classmethod
    async def fetch(cls: Type[BM], query, *args, convert: bool = True) -> Union[List[BM], List[Record]]:
        records = await cls.pool.fetch(query, *args)
        if cls is Model or convert is False:
            return records
        return [cls(**record) for record in records]

    @classmethod
    async def fetchrow(cls: Type[BM], query, *args, convert: bool = True) -> Union[BM, Record, None]:
        record = await cls.pool.fetchrow(query, *args)
        if cls is Model or record is None or convert is False:
            return record
        return cls(**record)

    @classmethod
    async def fetchval(cls, query, *args, column: int = 0):
        return await cls.pool.fetchval(query, *args, column=column)

    @classmethod
    async def execute(cls, query: str, *args) -> str:
        return await cls.pool.execute(query, *args)
