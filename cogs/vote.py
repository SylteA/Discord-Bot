from discord.ext import commands
import discord

from cogs.utils.votes import Vote
import asyncio


class Voting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll = Vote()
        self.removing = []

    @commands.command(name="poll")
    @commands.has_permissions(administrator=True)
    async def poll_(self, ctx, *, description):
        try:
            nMsg = description.split(",")
            desc = nMsg[0]
            args = nMsg[1:]
            await self.poll.add_poll(desc, args)

            emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]

            # DELETE PREVIOUS POLL
            async for msg in ctx.channel.history(limit=5):
                if msg.embeds and "previous poll" in msg.embeds[0].title.lower():
                    await msg.delete()
            # END DELETE PREVIOUS POLL

            # EDIT CURRENT POLL TO PREVIOUS POLL
            async for msg in ctx.channel.history(limit=5):
                if msg.embeds and "current poll" in msg.embeds[0].title.lower():
                    # CURRENT POLL PARSING
                    desc, options, votes = await self.poll.get_last_poll()
                    optionStr = ""
                    emojiopt1 = emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]
                    del emojiopt1[len(options):]
                    num = 0
                    for x, option in enumerate(options):
                        numtoemoji = emojiopt1[num]
                        optionStr = optionStr + numtoemoji + " - " + option.strip() + " (votes: " + str(votes[x]) + ")" + "\n"
                        num = x + 1
                    optionStr = optionStr[:-1]
                    em = discord.Embed(title = "**Previous Poll:**", description = f"{desc}\n\n{optionStr}", color=0x32363C)
                    # END PREVIOUS POLL PARSING
                    await msg.edit(embed=em)

                    await msg.clear_reactions()

            # END EDIT CURRENT POLL TO PREVIOUS POLL

            desc, options, votes = await self.poll.get_current_poll()
            votes = [0 for x in range(len(options))]

            numvotes = len(options) # Find the number of options.
            del emojiopt[numvotes:]

            optionStr = ""
            num = 0
            for x, option in enumerate(options):
                numtoemoji = emojiopt[num]
                optionStr = optionStr + numtoemoji + " - " + option.strip() + " (votes: " + str(votes[x]) + ")" + "\n"
                num = x + 1

            optionStr = optionStr[:-1]

            em = discord.Embed(title = "**Current Poll:**", description = f"{desc}\n\n{optionStr}", color=0x32363C)

            currentpoll = await ctx.send(embed=em)
            for emoji in emojiopt:
                await currentpoll.add_reaction(emoji)
        except Exception as err:
            em = discord.Embed(title="**Error**", description=f"Something went wrong! ```{err}```", color=0x32363C)
            await ctx.send(embed=em)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
    
        emoji = payload.emoji
        ruser = self.bot.get_user(payload.user_id)
        reactionmessage = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    
        emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]

        voteChannel = ["polls"]
        if "current poll" in reactionmessage.embeds[0].title.lower():
            if ruser == self.bot.user:
                return
            else:
                if str(reactionmessage.channel) in voteChannel and str(emoji) in emojiopt:
                    optionnum = emojiopt.index(str(emoji)) + 1
                
                    valid = await self.poll.add_vote(optionnum, ruser) 
                
                    if valid == -1:
                        self.removing.append((ruser, emoji))
                        await reactionmessage.remove_reaction(member = ruser, emoji=emoji)
                        await asyncio.sleep(3)
                        #ensure that this user doesnt get locked out of this incase remove failes to get called 
                        if (ruser, emoji) in self.removing:
                            self.removing.remove((ruser, emoji))
                    else:
                        #CURRENT POLL PARSING
                        desc, options, votes = await self.poll.get_current_poll()

                        optionStr = ""
                        num = 0
                        for x, option in enumerate(options):
                            numtoemoji = emojiopt[num]
                            optionStr = optionStr + numtoemoji + " - " + option.strip() + " (votes: " + str(votes[x]) + ")" + "\n"
                            num = x + 1

                        optionStr = optionStr[:-1]
                        em = discord.Embed(title = "**Current Poll:**", description = f"{desc}\n\n{optionStr}", color=0x32363C)
                        #END CURRENT POLL PARSING

                        '''msg = await reactionmessage.channel.history().get(author__name=self.bot.user.name)'''
                        async for msg in reactionmessage.channel.history(limit=5):
                            if msg.embeds and "current poll" in msg.embeds[0].title.lower():
                                await msg.edit(embed=em) #updated votes

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emoji = payload.emoji
        ruser = self.bot.get_user(payload.user_id)
        reactionmessage = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

        emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]

        voteChannel = ["polls"]
        if "current poll" in reactionmessage.embeds[0].title.lower():
            if str(reactionmessage.channel) in voteChannel and str(emoji) in emojiopt:
                if (ruser, emoji) in self.removing:
                    self.removing.remove((ruser, emoji))
                else:
                    optionnum = emojiopt.index(str(emoji)) + 1
                    valid = await self.poll.remove_vote(optionnum, ruser) 
    
                    #CURRENT POLL PARSING
                    desc, options, votes = await self.poll.get_current_poll()
                    if valid != -1:
                        optionStr = ""
                        num = 0
                        for x, option in enumerate(options):
                            numtoemoji = emojiopt[num]
                            optionStr = optionStr + numtoemoji + " - " + option.strip() + " (votes: " + str(votes[x]) + ")" + "\n"
                            num = x + 1
                        optionStr = optionStr[:-1]
                        em = discord.Embed(title = "**Current Poll:**", description = f"{desc}\n\n{optionStr}", color=0x32363C)
    
                        '''msg = await reactionmessage.channel.history().get(author__name=self.bot.user.name)'''
                        async for msg in reactionmessage.channel.history(limit=5):
                            if msg.embeds and "current poll" in msg.embeds[0].title.lower():
                                await msg.edit(embed=em) # updated votes
                    # END CURRENT POLL PARSING


def setup(bot):
    """Adds cog: Voting to bot"""
    bot.add_cog(Voting(bot))
