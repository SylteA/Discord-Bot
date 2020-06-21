import asyncio

"""I don't know where to put a call for this little func that checks for any changes 
in the roles of people and gives them points accordingly. Maybe use it as a cog? 
Have another cog call it?"""
# All of this new source code written by Pi
async def adder(bot):
    winner_role = bot.guild.get_role(692022273934360586)
    while bot.running:
        await asyncio.sleep(1800)
        old_states = current_states if len(current_states) != 0 else []
        current_winners = await bot.db.get_all_users(get_challenges=True, get_messages=False, get_reps=False)
        current_states = [(winner_role in winner.roles) for winner in current_winners]
        for state, user, old_state in zip(current_states, current_winners, old_states):
            if not old_state and state:
                user.add_cwin()
