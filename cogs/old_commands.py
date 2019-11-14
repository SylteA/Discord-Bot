from discord.ext import commands
import discord

from datetime import datetime
import pandas
import typing

from .utils.time import human_timedelta

# TODO: Checks for different commands
# TODO: Change cog name?


class OldCommands(commands.Cog, name='Commands'):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command()
    async def post_question(self, ctx):
        if self.bot.is_mod(ctx.author):
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
        await ctx.send(f"```Members: {ctx.guild.member_count}```")

    @commands.command()
    async def top_user(self, ctx):
        users = await self.bot.db.get_all_users(get_messages=True)
        users = sorted(users, key=lambda m: len(m.messages), reverse=True)
        # we need a way better way to resolve this.
        # Either we store a message_count per user already,
        # Or someone might know a faster query to fetch users + messages

        user = self.bot.get_user(users[0].id)
        if not isinstance(user, discord.User):
            return await ctx.send(f'Couldn\'t find the top user, but his ID is {user.id}'
                                  f'\n And he has `{len(users[0].messages)}`` messages')
        await ctx.send(f'Top User: {user} \nMessages: `{len(users[0].messages)}`')

    @commands.command()
    async def server_messages(self, ctx):
        messages = await self.bot.db.fetchrow('SELECT COUNT(*) FROM messages')
        count = messages['count']
        started_counting = datetime(year=2019, month=11, day=13)
        await ctx.send(f"I have read `{count}` messages after "
                       f"{human_timedelta(started_counting, suffix=False, brief=True, accuracy=2)}")

    @commands.command(name='messages', aliases=['my_messages'])
    async def messages_(self, ctx, member: typing.Optional[commands.MemberConverter]):
        member = member or ctx.author
        user = await self.bot.db.get_user(member.id, get_messages=True)
        await ctx.send(f"Messages: {len(user.messages)}"
                       f"\nSince: {human_timedelta(user.joined_at, suffix=False, brief=True, accuracy=2)}")

    def user__repr__(self, id: int) -> str:
        user = self.bot.get_user(id)
        if isinstance(user, discord.User):
            return f'{user.name}#{user.discriminator}'
        return f'(ID: {id})'

    @commands.command()
    async def scoreboard(self, ctx):
        # TODO: Improve the fetch.
        # Refer to to-do sentence in `.utils.DataBase.client`
        users = await self.bot.db.get_all_users(get_messages=True, get_reps=False)

        users_ = []
        for user in users:
            users_.append((self.user__repr__(user.id), len(user.messages)))

        users_.sort(key=lambda x: x[1], reverse=True)
        users_ = users_[:10]

        frame = pandas.DataFrame(users_, columns=["user", "messages"])
        frame.sort_values(by=['messages'], ascending=False)

        await ctx.send(f'```{frame.head().to_string(index=False)}```')

    @commands.command(name='reps', aliases=['my_reps'])
    async def reps_(self, ctx, member: typing.Optional[commands.MemberConverter]):
        user = await self.bot.db.get_user(get_reps=True)

        reps = len(user.reps)
        ret = f'{member.display_name} has received `{reps}` reps'
        if reps > 0:
            ret += f'\nLast rep: {human_timedelta(max(user.reps, key=lambda r: r.repped_at))}'

        await ctx.send(f'{member.display_name} has received {len(user.reps)}')

    @commands.command()
    async def rep_scoreboard(self, ctx):
        users = await self.bot.db.get_all_users(get_reps=True, get_messages=False)

        users_ = []
        for user in users:
            users_.append((self.user__repr__(user.id), len(user.reps)))

        users_.sort(key=lambda x: x[1], reverse=True)
        users_ = users_[:10]

        frame = pandas.DataFrame(users_, columns=["user", "reps"])
        frame.sort_values(by=['messages'], ascending=False)

        await ctx.send(f'```{frame.head().to_string(index=False)}```')

    @commands.command(name='rep')
    async def rep(self, ctx, member: commands.MemberConverter):
        if member.id == ctx.author.id:
            return await ctx.send('You cannot rep yourself.')

        user = await self.bot.db.get_user(member.id)

        result = await user.add_rep(message_id=ctx.message.id, author_id=ctx.author.id,
                                    extra_info={"channel_id": ctx.channel.id})

        if result is not None:
            return await ctx.send(f'You can rep that user again in {human_timedelta(result)}')
        else:
            await ctx.send(f"**{member.display_name}** has received a rep!")

    @commands.command(name='help')  # TODO: This needs updating.
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
