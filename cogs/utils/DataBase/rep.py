from datetime import datetime, timedelta
from json import dumps


class Rep(object):
    def __init__(self, bot, rep_id: int, user_id: int, author_id: int,
                 repped_at: datetime = datetime.utcnow(), extra_info: dict = None):
        self.bot = bot
        self.rep_id = rep_id  # In most cases this is the id of the message that posted this.
        self.user_id = user_id  # The user that recieved +1 rep.
        self.author_id = author_id  # The user that gave +1 rep.
        self.repped_at = repped_at
        self.extra_info = dumps(extra_info)

    async def post(self, assure_24h: bool = True):
        """We shouldn't have to check for duplicate reps either. ->
        Unless someone mis-uses this.
        If a conflict somehow still occurs nothing will happen. ( hopefully :shrug: )

        :param assure_24h:
            if True, this will only post the rep if the latest
            rep for this user_id is more than 24 hours ago.
        :return:
                        If posting is successful, returns None.
            If post is on cooldown, returns a datetime object on when the last rep was added.
        """
        if assure_24h:
            query = """SELECT * FROM reps 
                       WHERE author_id = $1 
                       ORDER BY repped_at ASC 
                       LIMIT 1"""

            record = await self.bot.db.fetch(query, self.author_id)
            if len(record) == 1:
                rep = Rep(bot=self.bot, **record[0])
                if (rep.repped_at + timedelta(days=1)) > datetime.utcnow():
                    return rep.repped_at

        query = """INSERT INTO reps ( rep_id, user_id, author_id, repped_at, extra_info )
                   VALUES (  $1, $2, $3, $4, $5 )
                   ON CONFLICT DO NOTHING"""
        await self.bot.db.execute(query, self.rep_id, self.user_id, self.author_id,
                                  self.repped_at, f"{self.extra_info}")
        return None
