import discord
import pandas as pd
from database import DataBase
import datetime
from discord.ext import commands
from votes import Vote
from discord.utils import get

token = ""

client = discord.Client()
bot = commands.Bot(command_prefix="t.")

# -------------------------------------------------------
# FUNCTI0ONS


def server_report(id):
    online = idle = offline = 0

    for m in id.members:
        if str(m.status) == "online":
            online += 1
        elif str(m.status) == "offline":
            offline += 1
        else:
            idle += 1

    return online, idle, offline

import re 
  
def find_urls(string): 
    # findall() has been used  
    # with valid conditions for urls in string 
    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string) 
    return url

def valid_url(urls):
    if len(urls) <= 0:
        return True
    
    valid_domains = ["hastebin", "pastebin", "youtube", "github", "techwithtim"]
    for url in urls:
        url = url.split("//")[1]
        if url.count("www.") >= 1:
            url = url.split(".")[1]
        else:
            url = url.split(".")[0]
            
        for domain in valid_domains:
            if domain in url:
                return True
    
    return False

# -------------------------------------------------------
# COMMANDS AND EVENTS
db = DataBase()

@client.event
async def on_ready():
    try:
        server_id = client.get_guild(501090983539245061)
        for channel in server_id.channels:
            if channel.name == 'faq':
                count = 0
                async for msg in channel.history(limit=500):
                    count += 1
                await channel.purge(limit=count)
    except Exception as e:
        print(e)
        print("failed to clear")
    await client.change_presence(activity=discord.Game(name='use the prefix "tim"'))


async def get_reacted_users():
    import random
    try:
        names = []
        server_id = client.get_guild(501090983539245061)
        for channel in server_id.channels:
            if channel.name == 'announcements':
                await channel.send("```The draw has begun!```")
                count = 0
                async for msg in channel.history(limit=4):
                    if count == 3:
                        users = await msg.reactions[0].users().flatten()

                        for name in users:
                            names.append(name)
                            #await channel.send(str(name.name))
                    count += 1

                # test
                await channel.send(f"```{len(names)} people have been entered! Picking Two Winners...```")
                r = random.randrange(0, len((names)))
                await channel.send(f"```*THE FIRST WINNER IS*``` {names[r].mention}")
                names.pop(r)
                r = random.randrange(0, len((names)))
                await channel.send(f"```*THE SECOND WINNER IS*``` {names[r].mention}")

                await channel.send(f"```You prizes will be sent to you via DM.```")
                break

    except Exception as e:
        print(e)

@client.event
async def on_member_join(member):
    global db
    server_id = client.get_guild(501090983539245061)
    db.update_server_stats(1)
    for channel in member.guild.channels:
        if channel.name == 'welcomes':
            await channel.send(f"Welcome to the Tech With Tim Community {member.mention}!\nMembers+=1\nCurrent Members: {server_id.member_count}")
            await channel.edit(topic="Current # of Members = " + str(server_id.member_count))

@client.event
async def on_message(message):
    global db
    await client.process_commands(message)
    server_id = client.get_guild(501090983539245061)
    commandChannels = ["commands", "bot-commands"]
    voteChannel = ["polls"]
    botChannel = ["faq"]

    mod_roles = ["mod", "admin", "helper", "tim"]
    poll = Vote()

    
    print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")

    mod = False
    for role in message.author.roles:
        if str(role).lower() in mod_roles:
            mod = True
            break
     
    '''if not(valid_url(find_urls(message.content.lower()))) and not(mod) and not(message.author.bot):
        await message.channel.purge(limit=1)
        #await message.channel.send(f"```The link you sent is not allowed on this server. {message.author.mention} If you believe this is a mistake contact a staff member.```" )'''
    if message.author.bot == False:

        msgg = message.content
        msg = message.content.lower()
        db.update_server_stats()

        if str(message.channel) in botChannel:
            if msg == "help":
                await message.channel.send("```Ask Tim BOT a question (its a serious work in progress)!```")
            else:
                if len(message.mentions) > 0:
                    print(message.mentions[0].id)
                    '''if message.mentions[0].id == 518054642979045377:
                        await message.channel.send("```" + chat(msg) + "```")'''

        if mod:
            if msg == "tim.post_question":
                await message.channel.purge(limit=1)
                await message.channel.send("```Please post your question, rather than asking for help. It's much easier and less time consuming.```")

        if msg == "tim.web" or msg == "tim.website":
            await message.channel.purge(limit=1)
            embed = discord.Embed(title="Tim's Website", description="[Visit the website!](https://techwithtim.net/)")
            await message.channel.send(content=None, embed=embed)

        if msg == "tim.docs" and str(message.channel) == "discord-bot-help":
            await message.channel.purge(limit=1)
            embed = discord.Embed(title="Discord Rewrite Docs", description="[View the Documentation Here!](https://discordpy.readthedocs.io/en/latest/)")
            await message.channel.send(content=None, embed=embed)

        if msg == "tim.git":
            await message.channel.purge(limit=1)
            embed = discord.Embed(title="Git Download Link",
                                  description="[Download GIT Here!](https://git-scm.com/downloads)")
            await message.channel.send(content=None, embed=embed)

        if msg == "tim.yt" or msg == "tim.youtube":
            await message.channel.purge(limit=1)
            embed = discord.Embed(title="Tech With Tim YouTube Channel!", description="[View Tim's Channel!](https://youtube.com/techwithtim)")
            await message.channel.send(content=None, embed=embed)

        if msg == "tim.twitter":
            await message.channel.purge(limit=1)
            embed = discord.Embed(title="Tech With Tim Twitter!", description="[View Tim's Twitter!](https://twitter.com/TechWithTimm)")
            await message.channel.send(content=None, embed=embed)

        if msg.find("tim.rep") == 0 and msg.count("tim.reps") == 0 and msg.count("tim.rep_scoreboard") == 0:
            try:
                if message.mentions[0] != message.author:
                    db.add_rep(message.mentions[0])
                    await message.channel.send(f"```{message.mentions[0]} has received a rep! ```")
                    role = message.author.guild.get_role(572289997613301760)
                    try:
                        await message.mentions[0].add_roles(role)
                    except:
                        pass
                else:
                    await message.channel.send(f"```You cannot rep yourself!!```")
            except Exception as e:
                print(e)
                await message.channel.send(f"```Invalid use of command. See \"tim.help\".```")

        if msg == "tim.insta" or msg == "tim.instagram":
            await message.channel.purge(limit=1)
            embed = discord.Embed(title="Tech With Tim Instagram!", description="[View Tim's Instagram!](https://instagram.com/tech_with_tim)")
            await message.channel.send(content=None, embed=embed)

        cmds = ["tim.help", "tim.scoreboard", "tim.rep_scorebaord", "tim.my_reps", "tim.member_count", "tim.top_user", "tim.users", "tim.server_messages", "tim.my_messages"]
        if msg in cmds and str(message.channel) not in commandChannels:
            await message.channel.send("**Please use #bot-commands channel**")

        if str(message.channel) in commandChannels:
            if msg == "tim.help":
                embed = discord.Embed(title="Tim Bot Help", description="A list of bot commands...")
                embed.add_field(name="tim.users", value="Gives status update on members of the server")
                embed.add_field(name="tim.top_user", value="Outputs the top users by (# of messages sent) in the server")
                embed.add_field(name="tim.my_messages", value="Outputs the # of messages you have sent")
                embed.add_field(name="tim.messages @user", value="Outputs the # of messages the mentioned user has sent")
                embed.add_field(name="tim.my_reps", value="Outputs the # of reps you have")
                embed.add_field(name="tim.reps @user",
                                value="Outputs the # of reps the mentioned user has")
                embed.add_field(name="tim.server_messages", value="Outputs the # of messages sent in the server")
                embed.add_field(name="tim.member_count", value="Outputs the # of members in the server")
                embed.add_field(name="tim.scoreboard", value="See a list of the top users by messages sent")
                embed.add_field(name="tim.rep_scoreboard", value="See a list of the top users by reps")
                embed.add_field(name="tim.web/tim.website", value="Links to Tim's website")
                embed.add_field(name="tim.git", value="Links to GIT download page")
                embed.add_field(name="tim.insta/tim.yt/tim.twitter", value="Links to Tim's Social Medias")
                await message.channel.send(content=None, embed=embed)

            elif msg == "tim.member_count":
                await message.channel.send(f"```Members: {server_id.member_count}```")

            elif msg == "tim.users":
                online, other, offline = server_report(server_id)
                await message.channel.send(f"```Online: {online}\nIdle/Busy: {other}\nOffline: {offline}```")

            elif msg == "tim.top_user":
                users, count = db.get_top_users()
                formatted = ""
                for user in users:
                    formatted += str(user.split("#")[0]) + ", "

                formatted = formatted[:-2]

                await message.channel.send(f"```Top User(s): {formatted}\nNumber of Messages: {count}```")

            elif msg == "tim.server_messages":
                count, day = db.get_all_messages()
                await message.channel.send(f"```Messages: {count}\nDays: {day}```")

            elif msg.count("tim.messages") == 1:
                try:
                    print(message.mentions)
                    count, date = db.get_msgs(message.mentions[0])
                    await message.channel.send(f"```Messages: {count}\nSince: {date}```")
                except:
                    await message.channel.send(f"```Invalid use of command. See \"tim.help\".```")

            elif msg == "tim.my_messages":
                count, date = db.get_msgs(message.author)
                await message.channel.send(f"```Messages: {count}\nSince: {date}```")

            elif msg == "tim.scoreboard":
                data = db.scoreboard()
                await message.channel.send(f"```{data}```")

            elif msg.find("tim.reps") == 0:
                try:
                    print(message.mentions)
                    count, date = db.get_rep(message.mentions[0])
                    await message.channel.send(f"```Reps: {count}\nLast Rep: {date}```")
                except:
                    await message.channel.send(f"```Invalid use of command. See \"tim.help\".```")

            elif msg == "tim.my_reps":
                count, date = db.get_rep(message.author)
                await message.channel.send(f"```Reps: {count}\nLast Rep: {date}```")

            elif msg == "tim.rep_scoreboard":
                data = db.rep_scoreboard()
                await message.channel.send(f"```{data}```")
        else:
            db.update_messages(message.author, 1)

            
            
            
            
            
@client.command()
@commands.has_permissions(administrator=True)
async def poll(ctx, *, description):
    try:
        nMsg = description.split(",")
        desc = nMsg[0]
        args = nMsg[1:]
        poll.add_poll(desc, args)

        emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]

        #DELETE PREVIOUS POLL
        async for msg in ctx.channel.history(limit=5):
            if msg.embeds and "previous poll" in msg.embeds[0].title.lower():
                await msg.delete()
        #END DELETE PREVIOUS POLL

        #EDIT CURRENT POLL TO PREVIOUS POLL
        async for msg in ctx.channel.history(limit=5):
            if msg.embeds and "current poll" in msg.embeds[0].title.lower():
                #CURRENT POLL PARSING
                desc, options, votes = poll.get_last_poll()
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
                #END PREVIOUS POLL PARSING

                await msg.clear_reactions()


        #END EDIT CURRENT POLL TO PREVIOUS POLL


        desc, options, votes = poll.get_current_poll()
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
    except:
        em = discord.Embed(title = "**Error**", description = "Something went wrong!", color=0x32363C)
        await ctx.send(embed=em)


@client.event
async def on_raw_reaction_add(payload):
    emoji = payload.emoji
    ruser = client.get_user(payload.user_id)
    reactionmessage = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    
    emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]

    voteChannel = ["polls"]
    if "current poll" in reactionmessage.embeds[0].title.lower():
        if ruser == client.user:
            return
        else:
            if str(reactionmessage.channel) in voteChannel and str(emoji) in emojiopt:
                optionnum = emojiopt.index(str(emoji)) + 1
                
                valid = poll.add_vote(optionnum, reactionmessage.author) 
                
                if valid == -1:
                    await reactionmessage.remove_reaction(member = ruser, emoji=emoji)
                else:
                    #CURRENT POLL PARSING
                    desc, options, votes = poll.get_current_poll()

                    optionStr = ""
                    num = 0
                    for x, option in enumerate(options):
                        numtoemoji = emojiopt[num]
                        optionStr = optionStr + numtoemoji + " - " + option.strip() + " (votes: " + str(votes[x]) + ")" + "\n"
                        num = x + 1

                    optionStr = optionStr[:-1]
                    em = discord.Embed(title = "**Current Poll:**", description = f"{desc}\n\n{optionStr}", color=0x32363C)
                    #END CURRENT POLL PARSING

                    msg = await reactionmessage.channel.history().get(author__name=client.user.name)
                    if "current poll" in msg.embeds[0].title.lower():  #checking if the last message is the current poll
                        await msg.edit(embed=em) #updated votes

                
                
        
            

            
@client.event
async def on_raw_reaction_remove(payload):
    emoji = payload.emoji
    ruser = client.get_user(payload.user_id)
    reactionmessage = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)

    emojiopt = [f"{x+1}\N{combining enclosing keycap}" for x in range(9)]

    voteChannel = ["polls"]
    if "current poll" in reactionmessage.embeds[0].title.lower():
        if str(reactionmessage.channel) in voteChannel and str(emoji) in emojiopt:
            optionnum = emojiopt.index(str(emoji)) + 1
            valid = poll.remove_vote(optionnum, reactionmessage.author) 

            #CURRENT POLL PARSING
            desc, options, votes = poll.get_current_poll()
            if valid != -1:
                optionStr = ""
                num = 0
                for x, option in enumerate(options):
                    numtoemoji = emojiopt[num]
                    optionStr = optionStr + numtoemoji + " - " + option.strip() + " (votes: " + str(votes[x]) + ")" + "\n"
                    num = x + 1
                optionStr = optionStr[:-1]
                em = discord.Embed(title = "**Current Poll:**", description = f"{desc}\n\n{optionStr}", color=0x32363C)

                msg = await reactionmessage.channel.history().get(author__name=client.user.name)
                if "current poll" in msg.embeds[0].title.lower():  #checking if the last message is the current poll
                    await msg.edit(embed=em) #updated votes        
            #END CURRENT POLL PARSING      

client.run(token)
