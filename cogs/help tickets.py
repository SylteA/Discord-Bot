from discord.ext import commands

help_ticket_channel = 727135440557310004  # *insert channel id here*


def setup(bot):
    bot.add_cog(HelpTickets(bot))


class HelpTickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['ticket', 'ask'])
    async def help_me(self, ctx, *, message):
        bot_channel = self.bot.get_channel(help_ticket_channel)
        member = ctx.message.author
        bot_chan_hist = await bot_channel.history(limit=200).flatten()
        if any([msg.content.startswith(f'Ticket Number: {member.id}') for msg in bot_chan_hist]):
            await ctx.send('There can  only be one... Ticket per person.')
        else:
            await bot_channel.send(f'Ticket Number: {member.id}\n{member} asked:\n\n{message}')
            await ctx.send('Ticket Created.\n Use `.thanks @user` to close the Ticket.')

    @commands.command(aliases=['solved', 'fix', 'thanks', 'solve', 'fixed', 'thank'])
    async def _delete(self, ctx, solver='Nobody', solver2=None):
        bot_channel = self.bot.get_channel(help_ticket_channel)
        member = ctx.author
        member_tag = f'<@!{ctx.author.id}>'
        print(member_tag)
        print(solver)
        if solver == member_tag:
            await ctx.send(f"Nice try, {member}. You can't reward yourself...")
        else:
            async for msg in bot_channel.history(limit=200):
                if msg.content.startswith(f'Ticket Number: {member.id}'):
                    await msg.delete()
                    await ctx.send(f'{solver} gets a cookie')
                    if solver2 is not None:
                        await ctx.send(f'{solver2} gets a cookie')

    @commands.command(aliases=['change', 're-ask'])
    async def edit(self, ctx, *, message):
        member = ctx.author
        bot_channel = self.bot.get_channel(help_ticket_channel)
        async for msg in bot_channel.history(limit=200):
            if msg.content.startswith(f'Ticket Number: {member.id}'):
                await msg.edit(content=f'Ticket Number: {member.id}\n{member} asked:\n\n{message}')
