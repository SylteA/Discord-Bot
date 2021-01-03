  
from discord.ext import commands
import discord
import random
import datetime
import json
now = datetime.datetime.now()

class useinfo(commands.Cog, name='Userinfo'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description = 'Information about a person.')
    async def userinfo(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
            embed=discord.Embed(title= f"User Information on @{member}", description=f'{member.mention}') 
            embed.add_field(name= f"Name", value= member, inline=True)
            embed.add_field(name='ID', value=member.id, inline=True)
            embed.add_field(name='Nickname', value=member.nick, inline=True)
            embed.add_field(name='Server', value=f'{ctx.guild.name}', inline=True)
            embed.add_field(name='Status', value=member.status, inline=True)
            embed.add_field(name='Activity', value=member.activity, inline=True)
            embed.add_field(name="Highest Role:", value=member.top_role.mention, inline=True)
            embed.set_thumbnail(url = member.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title= f"User Information on @{member}", description=f'{member.mention}') 
            embed.add_field(name= f"Name", value= member, inline=True)
            embed.add_field(name='ID', value=member.id, inline=True)
            embed.add_field(name='Nickname', value=member.nick, inline=True)
            embed.add_field(name='Server', value=f'{ctx.guild.name}', inline=True)
            embed.add_field(name='Status', value=member.status, inline=True)
            embed.add_field(name='Activity', value=member.activity, inline=True)
            embed.add_field(name="Highest Role:", value=member.top_role.mention, inline=True)
            embed.set_thumbnail(url = member.avatar_url)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(useinfo(bot))