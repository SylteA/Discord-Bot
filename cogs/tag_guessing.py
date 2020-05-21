from utils.tagguessing import mainHandler, Storage
from discord.ext import commands


class Commands(commands.Cog):
    def __init__(self, bot):
        self. bot = bot
        self.__docs__cache = None
        self.storage = Storage.Storage()
        self.tags = self.storage.load_tags()
        self.handler = mainHandler.mainHandler(list(self.tags.values()))


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        channel = self.bot.get_channel(payload.channel_id)
        if 'open_guesses' in self.storage.data and str(payload.message_id) in self.storage.data['open_guesses']:
            await self.handle_guess(payload, channel)

    # @commands.Cog.listener()
    async def handle_guess(self, payload, channel):
        if payload.user_id == 463166198335537162:
            msg = await channel.fetch_message(payload.message_id)
            if payload.emoji.name == '✅':
                self.handler.correct_guess(
                    msg.content[msg.content.index(';')+2:],
                    self.storage.data['open_guesses'][str(payload.message_id)])
                self.storage.dict_delete('open_guesses', str(payload.message_id))
            elif payload.emoji.name == '❌':
                self.storage.dict_delete('open_guesses', str(payload.message_id))
            elif payload.emoji.name == '❓':
                self.storage.add('wrong_guess', self.storage.data['open_guesses'][str(payload.message_id)])
                self.storage.dict_delete('open_guesses', str(payload.message_id))
                await channel.send(f'Biz, Please send wanted tag to {self.bot.command_prefix}wrong_guess')


    @commands.command()
    async def guess_tag(self, ctx):
        tag = ctx.message.content[ctx.message.content.index(' ')+1:].lower()
        response = self.handler.interpret(tag)
        emojis = ['✅', '❌', '❓']
        if response in self.tags.values():
            for k, v in self.tags.items():
                if v == response:
                    break
            msg = await ctx.send(f'Tag: {k}; {v}')
            for emoji in emojis:
                await msg.add_reaction(emoji=emoji)
            self.storage.dict_add('open_guesses', str(msg.id), tag)
        else:
            message = await ctx.send(response)
            if response.lower() == "could not determine from given text":
                self.storage.add('wrong_guess', tag)
                await message.add_reaction(emoji=emojis[2])

    @commands.command()
    async def wrong_guess(self, ctx):
        if 'wrong_guess' in self.storage.data:
            try:
                self.handler.correct_guess(self.tags[ctx.message.content[ctx.message.content.index(' ')+1:]],
                                               self.storage.data['wrong_guess'])
            except KeyError:
                await ctx.send("Error! No tag with that name found")
            else:
                self.storage.delete('wrong_guess')
                await ctx.send('Intents successfully updated')
        else:
            await ctx.send('No wrong guess in storage, try again')


def setup(bot):
    bot.add_cog(Commands(bot))


