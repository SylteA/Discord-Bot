from discord.ext import commands
import discord
from urllib.parse import urlparse
import re


class COCAnnouncer(commands.Cog, name='CoC Announcer'):
    def __init__(self, bot):
        self.bot = bot
        self.COC_CHANNEL = 0
        self.COC_ROLE = 0

    @commands.command(name='coc')
    async def invite(self, ctx: commands.Context, *, url: str = None):
        """invite all active COC Group members to compete"""
        if ctx.channel is None or ctx.channel.id != self.COC_CHANNEL:
            return
        await ctx.message.delete()
        if url is None:
            embed = discord.Embed(
                    title='COC Invite',
                    description=f'You\'d need to provide a valid URL for the invite.',
                    footer='Self destruct in 30s')
            await ctx.send(embed=embed, delete_after=30)
        res, parsed = check_url(url)
        if not res:
            embed = discord.Embed(
                    title='COC Invite',
                    description=parsed,
                    footer='Self destruct in 30s')
            await ctx.send(embed=embed, delete_after=30)
        else:
            mentions = []
            guild = ctx.guild
            role = guild.get_role(self.COC_ROLE)
            for user in role.members:
                if user.status in [discord.Status.online, discord.Status.idle]:
                    mentions.append(f'<@{user.id}>')
            if len(mentions) > 0:
                embed = discord.Embed(
                        title='COC Invite',
                        description=f'Join COC at {parsed}',
                        footer='Self destruct in 5 mins.')
                embed.add_field(name='Invitees', value=", ".join(mentions), inline=False)
                await ctx.send(embed=embed, delete_after=300)


def check_url(text):
    urls = re.findall(r"(https?://[^\s]+)", text, flags=re.IGNORECASE)
    if len(urls) == 0:
        return False, 'Please provide a valid url'  # Not a URL
    elif len(urls) > 1:
        return False, 'Please provide a single url'  # devour multiple URLs
    elif urlparse(urls[0]).netloc != 'www.codingame.com':
        return False, 'Only CoC URLs are supported'  # Not a valid URL
    return True, urls[0]


def setup(bot):
    bot.add_cog(COCAnnouncer(bot))
