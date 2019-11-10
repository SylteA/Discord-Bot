from discord.ext import commands
import discord

import typing

# TODO: Checks for different commands
# TODO: Change cog name?


class OldCommands(commands.Cog, name='Commands'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')
        self.is_mod = self.bot.is_mod

    @commands.command()
    async def post_question(self, ctx):
        if self.is_mod(ctx.author):
            await ctx.message.delete()
            await ctx.send("```Please post your question, rather than asking for help. "
                           "It's much easier and less time consuming.```")

    @commands.command(name='website', aliases=['web'])
    async def web_(self, ctx):
        embed = discord.Embed(title="Tim's Website", description="[Visit the website!](https://techwithtim.net/)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def docs(self, ctx):
        embed = discord.Embed(title="Discord Rewrite Docs",
                              description="[View the Documentation Here!](https://discordpy.readthedocs.io/en/latest/)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def git(self, ctx):
        embed = discord.Embed(title="Git Download Link",
                              description="[Download GIT Here!](https://git-scm.com/downloads)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(name='youtube', aliases=['yt'])
    async def yt_(self, ctx):
        embed = discord.Embed(title="Tech With Tim YouTube Channel!",
                              description="[View Tim's Channel!](https://youtube.com/techwithtim)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def twitter(self, ctx):
        embed = discord.Embed(title="Tech With Tim Twitter!",
                              description="[View Tim's Twitter!](https://twitter.com/TechWithTimm)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    @commands.command(name='instagram', aliases=['insta'])
    async def insta_(self, ctx):
        embed = discord.Embed(title="Tech With Tim Instagram!",
                              description="[View Tim's Instagram!](https://instagram.com/tech_with_tim)")
        await ctx.message.delete()
        await ctx.send(embed=embed)

    def members(self):
        members = set(self.bot.get_all_members())
        d = {'online': 0, 'idle': 0, 'dnd': 0, 'offline': 0}
        for member in members:
            d[str(member.status)] += 1
        return d

    @commands.command()
    async def users(self, ctx):
        members = self.members()
        await ctx.send(f'```Online: {members["online"]}\n'
                       f'Idle: {members["idle"]}\n'
                       f'DND: {members["dnd"]}\n'
                       f'Offline: {members["offline"]}')

    @commands.command()
    async def member_count(self, ctx):
        await ctx.send(f"```Members: {self.bot.guild.member_count}```")

    @commands.command()
    async def top_user(self, ctx):
        users, count = self.bot.db.get_top_users()
        formatted = ""
        for user in users:
            formatted += str(user.split("#")[0]) + ", "

        formatted = formatted[:-2]

        await ctx.send(f"```Top User(s): {formatted}\nNumber of Messages: {count}```")

    @commands.command()
    async def server_messages(self, ctx):
        count, day = self.bot.db.get_all_messages()
        await ctx.send(f"```Messages: {count}\nDays: {day}```")

    @commands.command(name='messages', aliases=['my_messages'])
    async def messages_(self, ctx, member: typing.Optional[commands.MemberConverter]):
        member = member or ctx.author
        count, date = self.bot.db.get_msgs(member)
        await ctx.send(f"```Messages: {count}\nSince: {date}```")

    @commands.command()
    async def scoreboard(self, ctx):
        data = self.bot.db.scoreboard()
        await ctx.send(f"```{data}```")

    @commands.command(name='reps', aliases=['my_reps'])
    async def reps_(self, ctx, member: typing.Optional[commands.MemberConverter]):
        member = member or ctx.author
        count, date = self.bot.db.get_rep(member)
        await ctx.send(f"```Reps: {count}\nLast Rep: {date}```")

    @commands.command()
    async def rep_scoreboard(self, ctx):
        data = self.bot.db.rep_scoreboard()
        await ctx.send(f"```{data}```")

    @commands.command(name='rep')
    @commands.cooldown(1, 60*60*24, commands.BucketType.member)
    async def rep(self, ctx, member: commands.MemberConverter):
        if member.id == ctx.author.id:
            return await ctx.send('You cannot rep yourself.')

        self.bot.db.add_rep(member)
        await ctx.send(f"```{member} has received a rep!```")

    @commands.command(name='help')
    async def help_(self, ctx):
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
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(OldCommands(bot))
