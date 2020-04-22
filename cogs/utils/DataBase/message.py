from datetime import datetime

from discord import Guild, TextChannel, Message as Discord_Message


class CouldNotFind(Exception):
    """Raised when `Message.get_real()` doesnt find `x`"""


class Message(object):
    def __init__(self, bot, created_at: datetime, content: str,
                 message_id: int, channel_id: int, guild_id: int, author_id: int):
        self.bot = bot
        self.created_at = created_at
        self.content = content
        self.message_id = message_id
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.author_id = author_id

    async def post(self) -> None:
        """We shouldn't have to check for duplicate messages here ->
        Unless someone mis-uses this.
        If a conflict somehow still occurs nothing will happen. ( hopefully :shrug: )"""
        query = """INSERT INTO messages ( message_id, guild_id, channel_id, author_id, content, created_at )
                   VALUES ( $1, $2, $3, $4, $5, $6 )
                   ON CONFLICT DO NOTHING"""
        await self.bot.db.execute(query, self.message_id, self.guild_id, self.channel_id, self.author_id,
                                  self.content, self.created_at)

    async def get_real(self) -> Discord_Message:
        """Get the "real" message object
        Highly recommended to try: except `message.CouldNotFind`"""
        guild = self.bot.get_guild(self.guild_id)
        if not isinstance(guild, Guild):
            raise CouldNotFind

        channel = guild.get_channel(self.channel_id)
        if not isinstance(channel, TextChannel):
            raise CouldNotFind

        message = await channel.fetch_message(self.message_id)
        if not isinstance(message, Discord_Message):
            raise CouldNotFind

        return message

    @classmethod
    async def on_message(cls, bot, message: Discord_Message) -> None:
        user = await bot.db.get_user(message.author.id)  # Assure that everyone gets a user row
        self = cls(bot=bot, content=message.content, created_at=message.created_at,
                   message_id=message.id, guild_id=message.guild.id,
                   channel_id=message.channel.id, author_id=message.author.id)
        await self.post()
        await bot.db.execute('UPDATE users SET messages_sent = messages_sent + 1 WHERE id = $1', user.id)
