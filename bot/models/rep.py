from datetime import datetime, timedelta

from pydantic import Field

from .model import Model


class Rep(Model):
    rep_id: int
    user_id: int
    author_id: int
    repped_at: datetime = Field(default_factory=datetime.utcnow)
    extra_info: str = ""

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
                       ORDER BY repped_at DESC
                       LIMIT 1"""

            rep = await self.fetchrow(query, self.author_id)
            if rep:
                if (rep.repped_at + timedelta(days=1)) > datetime.utcnow():
                    return rep.repped_at

        query = """INSERT INTO reps ( rep_id, user_id, author_id, repped_at, extra_info )
                   VALUES (  $1, $2, $3, $4, $5 )
                   ON CONFLICT DO NOTHING"""
        await self.execute(
            query,
            self.rep_id,
            self.user_id,
            self.author_id,
            self.repped_at,
            f"{self.extra_info}",
        )
        return None
