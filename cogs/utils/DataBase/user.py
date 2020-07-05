from discord import Member, User as Discord_User

from datetime import datetime
from typing import List, Union

from .message import Message
from .rep import Rep


class User(object):
    def __init__(self, bot, id: int, *, messages: List[Message], reps: List[Rep],
                 commands_used: int = 0, joined_at: datetime = datetime.utcnow(),
                 messages_sent: int = 0):
        self.bot = bot
        self.id = id
        self.messages = messages
        self.commands_used = commands_used
        self.messages_sent = messages_sent
        self.reps = reps
        self.joined_at = joined_at
        # Joined at wont actually be when they joined.
        # It will be when they "joined" the database

    async def post(self) -> None:
        """We shouldn't have to check for duplicate messages here ->
        Unless someone mis-uses this.
        If a conflict somehow still occurs nothing will happen. ( hopefully :shrug: )"""
        query = """SELECT * FROM users WHERE id = $1"""
        assure_exclusive = await self.bot.db.fetch(query, self.id)
        if len(assure_exclusive) == 0:
            query = """INSERT INTO users ( id, commands_used, joined_at, messages_sent )
                    VALUES ( $1, $2, $3, $4 )
                    ON CONFLICT DO NOTHING"""
            await self.bot.db.execute(query, self.id, self.commands_used, self.joined_at, self.messages_sent)

    @classmethod
    async def on_command(cls, bot, user: Union[Member, Discord_User]):
        await bot.db.get_user(user.id, get_messages=False)  # Assure a user object in database.

        query = """UPDATE users SET commands_used = commands_used + 1 WHERE id = $1"""
        await bot.db.execute(query, user.id)

    async def add_rep(self, message_id: int, author_id: int,
                      repped_at: datetime = datetime.utcnow(), extra_info: dict = None,
                      assure_24h: bool = True):
        """
        Add a rep using `self.id` as user_id
        :param message_id:
            passed to rep_id
        :param author_id:
            The user that repped `self`
        :param repped_at:
            datetime object for when the rep was added
        :param extra_info:
            dict
        :param assure_24h:
                        if True, this will only post the rep if the latest
            rep for this user_id is more than 24 hours ago.
        :return:
            If posting is successful, returns None.
            If post is on cooldown, returns a datetime object on when the last rep was added.
        """
        rep = Rep(bot=self.bot, rep_id=message_id, user_id=self.id, author_id=author_id,
                  repped_at=repped_at, extra_info=extra_info)
        return await rep.post(assure_24h=assure_24h)
