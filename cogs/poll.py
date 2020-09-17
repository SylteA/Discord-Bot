import discord
from discord.ext import commands

import datetime
import re


class Polls(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.__bot = bot

    @property
    def reactions(self):
        return {
            1: '1️⃣',
            2: '2️⃣',
            3: '3️⃣',
            4: '4️⃣',
            5: '5️⃣',
            6: '6️⃣',
            7: '7️⃣',
            8: '8️⃣',
            9: '9️⃣',
            10: '🔟'
        }

    def poll_check(self, message: discord.Message):
        try:
            embed = message.embeds[0]
        except:
            return False
        if str(embed.footer.text).count("Poll by") == 1:
            return message.author == self.__bot.user
        return False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        channel: discord.TextChannel = self.__bot.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)

        if payload.user_id == self.__bot.user.id:
            return

        if not self.poll_check(message):
            return

        emojis = list(self.reactions.values())
        if str(payload.emoji) not in emojis:
            return

        for reaction in message.reactions:
            if str(reaction) not in emojis:
                return

            if str(reaction.emoji) != str(payload.emoji):
                user = self.__bot.get_user(payload.user_id)
                await message.remove_reaction(reaction.emoji, user)

    @commands.group()
    async def poll(self, ctx):
        """ Polls """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(self.__bot.get_command('poll'))

    @poll.command()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def new(self, ctx, desc: str, *choices):
        """ Create a new poll """
        await ctx.message.delete()
        
        if len(choices) < 2:
            ctx.command.reset_cooldown(ctx)
            if len(choices) == 1:
                return await ctx.send("Can't make a poll with only one choice")
            return await ctx.send("You have to enter two or more choices to make a poll")

        if len(choices) > 10:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't make a poll with more than 10 choices")

        embed = discord.Embed(description=f"**{desc}**\n\n"+"\n\n".join(
                                  f"{str(self.reactions[i])}  {choice}" for i, choice in enumerate(choices, 1)),
                              timestamp=datetime.datetime.utcnow(), color=discord.colour.Color.gold())
        embed.set_footer(text=f"Poll by {str(ctx.author)}")
        msg = await ctx.send(embed=embed)
        for i in range(1, len(choices) + 1):
            await msg.add_reaction(self.reactions[i])

    @poll.command()
    async def show(self, ctx, message: str):
        """Show a poll result"""
        await ctx.message.delete()
        
        try:
            *_, channel_id, msg_id = message.split("/")

            try:
                channel = self.__bot.get_channel(int(channel_id))
                message = await channel.fetch_message(int(msg_id))
            except:
                return await ctx.send("Please provide the message ID/link for a valid poll")
        except:
            try:
                message = await ctx.channel.fetch_message(message)
            except:
                return await ctx.send("Please provide the message ID/link for a valid poll")

        if self.poll_check(message):
            poll_embed = message.embeds[0]
            reactions = message.reactions
            reactions_total = sum([reaction.count - 1 if str(reaction.emoji) in self.reactions.values() else 0
                                   for reaction in reactions])

            options = list(map(lambda o:' '.join(o.split()[1:]), poll_embed.description.split('1️')[1].split("\n\n")))
            desc = poll_embed.description.split('1️')[0]

            embed = discord.Embed(description=desc, timestamp=poll_embed.timestamp, color=discord.Color.gold())

            for i, option in enumerate(options):
                reaction_count = reactions[i].count - 1
                indicator = "░"*20
                if reactions_total != 0:
                    indicator = ("█" * int(((reaction_count / reactions_total) * 100) / 5) +
                                 "░" * int((((reactions_total - reaction_count) / reactions_total) * 100) / 5))

                embed.add_field(name=option, value=f"{indicator}  {int((reaction_count / (reactions_total or 1)*100))}%"
                                                   f" (**{reaction_count} votes**)", inline=False)

            embed.set_footer(text="Poll Result")
            return await ctx.send(embed=embed)

        return await ctx.send("Please provide the message ID/link for a valid poll")


def setup(bot):
    bot.add_cog(Polls(bot))
