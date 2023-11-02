import discord
from discord.ext import commands

from bot import core
from bot.config import settings
from bot.extensions.clashofcode.utils import coc_helper


class ClashOfCodeEvents(commands.Cog):
    """Events for clash of code in discord."""

    def __init__(self, bot: core.DiscordBot):
        self.bot = bot

    @property
    def role(self):
        return self.bot.guild.get_role(settings.coc.role_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if coc_helper.session_message != 0:
            if payload.message_id == coc_helper.session_message:
                if str(payload.emoji) == "🖐️":
                    if payload.user_id not in coc_helper.session_users:
                        coc_helper.session_users.append(payload.user_id)

        if payload.message_id != settings.coc.message_id:
            return

        if self.role in payload.member.roles:
            return

        await payload.member.add_roles(self.role)
        try:
            await payload.member.send(f"Gave you the **{self.role.name}** role!")
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if coc_helper.session_message != 0:
            if payload.message_id == coc_helper.session_message:
                if str(payload.emoji) == "🖐️":
                    if payload.user_id in coc_helper.session_users:
                        coc_helper.session_users.remove(payload.user_id)

        if payload.message_id != settings.coc.message_id:
            return

        member = self.bot.guild.get_member(payload.user_id)
        if self.role not in member.roles:
            return

        await member.remove_roles(self.role)
        try:
            await member.send(f"Removed your **{self.role.name}** role!")
        except discord.HTTPException:
            pass
