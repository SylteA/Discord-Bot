import discord #imports discord 
from discord.ext import commands # and commands

class Voting(commands.Cog): 
    #creats a cog
    def __init__(self, bot):
        self.bot = bot # makes self.bot be our bot variable
        
    #code here

def setup(bot): #this gets called when we start load this extension
    bot.add_cog(Voting(bot)) # adds the cog voting with our bot variable.
