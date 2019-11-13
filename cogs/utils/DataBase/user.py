# Currently excluding `messages` from this class until i learn more about relations :) - Sylte
# If someone else can include *this* then please do!
# *this*: When fetching a Member with  `.client.DataBase().get_member()` the messages stored in the `messages` table are
# Also automaticly fetched.
# Until then we need to fetch messages separately using other utils i will make in `.client.DataBase`

from discord import Member, User as Discord_User

from datetime import datetime
from typing import List, Union

from .message import Message


class User(object):
    def __init__(self, bot, id: int, *, messages: List[Message] = None,
                 commands_used: int = 0, reps: int, joined_at: datetime = datetime.utcnow()):
        self.bot = bot
        self.id = id
        self.messages = messages
        self.commands_used = commands_used
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
            query = """INSERT INTO users ( id, commands_used, joined_at )
                    VALUES ( $1, $2, $3 )
                    ON CONFLICT DO NOTHING"""
            await self.bot.db.execute(query, self.id, self.commands_used, self.joined_at)

    @classmethod
    async def on_command(cls, bot, user: Union[Member, Discord_User]):
        await bot.db.raw_user(user.id)  # Assure a user object in database.

        query = """UPDATE users SET commands_used = commands_used + 1 WHERE id = $1"""
        await bot.db.execute(query, user.id)



