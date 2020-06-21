class CWins(object):
    def __init__(self, bot, user, wins = 0):
        self.id = user
        self.bot = bot
        self.wins = wins

    async def add_win(self):
        """Adds +1 to the win count for the user in the challenge leaderboard.
        No need to check if they already have an entry because they are supposed
        to already have an entry in the user db."""

        query = """UPDATE users SET wins = wins + 1 WHERE id = $1"""
        self.bot.db.execute(query, self.id)
        self.wins += 1
        # Idk how to actually get info out of the db so I suppose as long as
        # this works fine, I think self.wins will be synced with the value in the db

        return self.wins
