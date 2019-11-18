from datetime import datetime
from json import dumps
import discord


class Poll(object):
    def __init__(self, bot, guild_id: int, channel_id: int, message_id: int, author_id: int, description: str,
                 options: dict, replies: dict, created_at: datetime):
        self.bot = bot
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id
        self.author_id = author_id
        self.description = description
        self.options = options
        self.replies = replies
        self.created_at = created_at

        self.reactions = {
            '1️⃣': '1',
            '2️⃣': '2',
            '3️⃣': '3',
            '4️⃣': '4',
            '5️⃣': '5',
            '6️⃣': '6',
            '7️⃣': '7',
            '8️⃣': '8',
            '9️⃣': '9',
            '🔟': '10'
        }

        self.guild = None
        self.channel = None
        self.message = None

    async def post(self):
        query = """INSERT INTO polls ( guild_id, author_id, channel_id, message_id, 
                                       description, options, replies, created_at )
                   VALUES ( $1, $2, $3, $4, $5, $6, $7, $8 )"""
        await self.bot.db.execute(query, self.guild_id, self.author_id, self.channel_id, self.message_id,
                                  self.description, dumps(self.options), dumps(self.replies), self.created_at)

    async def _update(self):
        query = """UPDATE polls SET options = $2, replies = $3 WHERE guild_id = $1"""
        await self.bot.db.execute(query, self.guild_id, dumps(self.options), dumps(self.replies))

    async def _listener(self):
        def check(p):
            return (
                p.message_id == self.message_id
                and p.user_id != self.bot.user.id
            )
        while not self.bot.is_closed():
            payload = await self.bot.wait_for('raw_reaction_add', check=check)
            await self.handle_payload(payload)

    async def handle_payload(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        emoji = payload.emoji.name
        vote = self.reactions.get(emoji, None)
        if vote is None:
            return
        if str(payload.user_id) in self.replies:
            return await self.message.remove_reaction(emoji, self.guild.get_member(payload.user_id))
        self.replies[str(payload.user_id)] = vote
        await self._update()
        await self.message.remove_reaction(emoji, self.guild.get_member(payload.user_id))
        await self.channel.send(f'Thank you {self.bot.get_user(payload.user_id)} for voting, any further attempts '
                                f'to vote will be ignored.', delete_after=5.0)

    def clean_reactions(self) -> dict:
        new_dict = {}
        for index, option in self.options.items():
            for reaction, index2 in self.reactions.items():
                if index == index2:
                    new_dict[reaction] = index
        return new_dict

    async def react(self):
        self.reactions = self.clean_reactions()
        if not self.guild.me.permissions_in(self.channel).add_reactions:
            raise RuntimeWarning('Failed to react to pool - Missing ADD_REACTIONS permission')
        if not self.guild.me.permissions_in(self.channel).manage_messages:
            raise RuntimeWarning('Failed to react to pool - Missing MANAGE_MESSAGES permission')
        for emote in self.reactions:
            await self.message.add_reaction(emote)

    async def listen(self):
        try:
            self.guild = self.bot.get_guild(self.guild_id)
            self.channel = self.guild.get_channel(self.channel_id)
            self.message = await self.channel.fetch_message(self.message_id)
        except discord.NotFound:
            return
        try:
            await self.react()
        except RuntimeWarning as e:
            return await self.channel.send(str(e))
        return self.bot.loop.create_task(self._listener())

    @staticmethod
    def _enumerate_emote(num: int):
        if num > 10 or num < 0:
            raise RuntimeWarning('Can only display numbers between 0 to 10')
        if num == 10:
            return '\N{KEYCAP TEN}'
        return f'{num}\N{COMBINING ENCLOSING KEYCAP}'

    def _display_options(self, options: dict) -> str:
        string = ""
        for index, option in enumerate(options.values()):
            string += f'{self._enumerate_emote(index + 1)}: {option}\n'
        return string

    # TODO: Display current votes.
    async def display(self, ctx) -> discord.Message:
        embed = discord.Embed(description=self.description)
        embed.add_field(name='Options:', value=self._display_options(self.options))
        return await ctx.send(embed=embed)
