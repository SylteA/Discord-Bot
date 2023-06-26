from datetime import datetime
from typing import Optional, Union

import discord
from pydantic import Field

from .model import Model


class User(Model):
    id: int
    commands_used: int = 0
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    messages_sent: int = 0

    async def post(self) -> None:
        """We shouldn't have to check for duplicate messages here ->
        Unless someone mis-uses this.
        If a conflict somehow still occurs nothing will happen. ( hopefully :shrug: )"""
        query = """SELECT count(*) FROM users WHERE id = $1"""
        assure_exclusive = await self.fetchval(query, self.id)
        if assure_exclusive == 0:
            query = """INSERT INTO users ( id, commands_used, joined_at, messages_sent )
                    VALUES ( $1, $2, $3, $4 )
                    ON CONFLICT DO NOTHING"""
            await self.execute(query, self.id, self.commands_used, self.joined_at, self.messages_sent)

    @classmethod
    async def fetch_user(cls, user_id: int, create_if_no_exist=True) -> Optional["User"]:
        query = """SELECT * FROM users WHERE id = $1"""
        user = await cls.fetchrow(query, user_id)
        if user is None and create_if_no_exist:
            user = cls(id=user_id)
            await user.post()
        return user

    @classmethod
    async def on_command(cls, user: Union[discord.Member, discord.User]):
        await cls.fetch_user(user.id)
        query = """UPDATE users SET commands_used = commands_used + 1 WHERE id = $1"""
        await cls.execute(query, user.id)

    @classmethod
    async def on_message(cls, user: Union[discord.Member, discord.User]):
        await cls.fetch_user(user.id)
        query = """UPDATE users SET messages_sent = messages_sent + 1 WHERE id = $1"""
        await cls.execute(query, user.id)
