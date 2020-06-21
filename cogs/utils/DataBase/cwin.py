class CWins(object):
    def __init__(self, bot, user, wins = 0):
        self.id = user
        self.bot = bot
        self.wins = wins

    async def add_win(self):
        """Adds +1 to the win count for the user in the challenge leaderboard
        and creates them an entry if they don't have one"""
        query = """SELECT * FROM challenges WHERE id = $1"""
        assure = await self.bot.db.fetch(query, self.id)
        if len(assure) == 0:
            query = """INSERT INTO challenges ( id, wins )
                            VALUES ( $1, $2 )
                            ON CONFLICT DO NOTHING"""
            await self.bot.db.execute(query, self.id, self.wins)

        query = """UPDATE challenges SET wins = wins + 1 WHERE id = $1"""
        self.bot.db.execute(query, self.id)
        self.wins += 1
        # Idk how to actually get info out of the db so I suppose as long as
        # this works fine, I think self.wins will be synced with the value in the db

        return self.wins
