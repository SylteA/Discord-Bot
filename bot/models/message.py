from datetime import datetime

from discord import Message as Discord_Message

from .model import Model
from .user import User


class Message(Model):
    created_at: datetime
    content: str
    message_id: int
    channel_id: int
    guild_id: int
    author_id: int

    async def post(self) -> None:
        """We shouldn't have to check for duplicate messages here ->
        Unless someone mis-uses this.
        If a conflict somehow still occurs nothing will happen. ( hopefully :shrug: )"""

        query = """INSERT INTO messages ( message_id, guild_id, channel_id, author_id, content, created_at )
                   VALUES ( $1, $2, $3, $4, $5, $6 )
                   ON CONFLICT DO NOTHING"""
        await self.execute(
            query,
            self.message_id,
            self.guild_id,
            self.channel_id,
            self.author_id,
            self.content,
            self.created_at.replace(tzinfo=None),
        )

    @classmethod
    async def on_message(cls, message: Discord_Message) -> None:
        self = cls(
            content=message.content,
            created_at=message.created_at,
            message_id=message.id,
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            author_id=message.author.id,
        )
        await self.post()
        await User.on_message(message.author)
