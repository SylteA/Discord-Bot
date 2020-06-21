import asyncio

"""I don't know where to put a call for this little func that checks for any changes 
in the roles of people and gives them points accordingly. Maybe use it as a cog? 
Have another cog call it?"""
# All of this new source code written by Pi
async def adder(bot):
    winner_role = bot.guild.get_role(692022273934360586)
    current_winners = []
    while bot.running:
        await asyncio.sleep(1800)
        old_winners = current_winners
        current_winners = winner_role.members()
        for winner in current_winners:
            if winner not in old_winners:
                winner.add_cwin()
