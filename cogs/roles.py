import discord
from discord.ext import commands

from config import DEVELOPER_ROLE_ID, REACTION_ROLES, REACTION_ROLES_MESSAGE_ID


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot=bot))


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def lvl_20_role(self):
        return self.bot.guild.get_role(DEVELOPER_ROLE_ID)

    @property
    def roles(self) -> dict:
        return {int(emoji_id): self.bot.guild.get_role(role_id) for emoji_id, role_id in REACTION_ROLES}
        # {
        #     736112775352287232: self.bot.guild.get_role(740689745532682290),  # python
        #     737030552770576395: self.bot.guild.get_role(740691624979333272),  # csharp
        #     740694148876599409: self.bot.guild.get_role(740690985926787093),  # js
        #     740694256053911675: self.bot.guild.get_role(740690527325782038),  # java
        #     740694321216356564: self.bot.guild.get_role(740691348977352754),  # ruby
        # }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != REACTION_ROLES_MESSAGE_ID:
            return

        if (
            any(role in payload.member.roles for role in self.roles.values())
            or self.lvl_20_role not in payload.member.roles
        ):
            message = await self.bot.get_channel(payload.channel_id).fetch_message(REACTION_ROLES_MESSAGE_ID)
            return await message.remove_reaction(payload.emoji, payload.member)

        await payload.member.add_roles(self.roles[payload.emoji.id])
        try:
            await payload.member.send(f"Gave you the **{self.roles[payload.emoji.id].name}** role!")
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        member = self.bot.guild.get_member(payload.user_id)
        if payload.message_id != REACTION_ROLES_MESSAGE_ID:
            return

        if self.roles[payload.emoji.id] not in member.roles or self.lvl_20_role not in member.roles:
            return

        await member.remove_roles(self.roles[payload.emoji.id])
        try:
            await member.send(f"Removed your **{self.roles[payload.emoji.id].name}** role!")
        except discord.HTTPException:
            pass
