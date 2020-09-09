import discord
from discord.ext import commands

import datetime
import asyncio


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot=bot))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ttp = []  # Temp Tim Pings :p
        self.staff_roles = [580911082290282506,  # admin
                            511332506780434438,  # mod
                            541272748161499147,  # helper
                            511334601977888798]  # tim

    @property
    def report_channel(self):
        return self.bot.get_channel(749742688521158656)

    @property
    def muted_role(self):
        return self.bot.get_guild(501090983539245061).get_role(583350495117312010)

    async def am_action(self, channel, member, action, reason):
        embed = discord.Embed()

        if action == "mute":
            await member.add_roles(self.muted_role, reason=reason)
            embed.title = "Mute"
            embed.description = f"{member.mention} got muted for `{reason}`"
            await channel.send(embed=embed)

        elif action == "report":
            embed.title = "Report"
            embed.description = f"{member.mention} got reported for `{reason}`"

        else:
            raise ValueError(f"Action '{action}' not found")

        await self.report_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or any(role in message.author.roles for role in self.staff_roles):
            return

        mentions = [x for x in message.mentions if not x.bot]

        if len(mentions) > 5:
            await self.am_action(message.channel, message.author, "mute", "Mass mention")
            pings = "**Members who got pinged**\n" + ", ".join(x.mention for x in mentions)
            await self.report_channel.send(embed=discord.Embed(description=pings))

        elif 501089409379205161 in [x.id for x in mentions]:  # if pinged tim
            if message.author.id in self.ttp:
                await self.am_action(message.channel, message.author, "mute", "Tim ping (twice)")

            else:
                await self.am_action(message.channel, message.author, "report", "Tim ping")
                await message.channel.send(f"{message.author.mention} Please **do not** ping Tim, it's in"
                                           f" <#511343933415096323>, pinging Tim again will result in a mute.")

                self.ttp.append(message.author.id)
                await asyncio.sleep(36000.0)
                self.ttp.remove(message.author.id)

    @commands.command("report")
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def report(self, ctx, member: discord.Member, *, reason: str):
        """Report a user to staff for a reason."""
        await ctx.message.delete()

        if member.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't report a bot <:mhm:687726663676592145>")

        if member.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't report your self <:mhm:687726663676592145>")

        thx_embed = discord.Embed(title="Report", timestamp=datetime.datetime.utcnow())
        thx_embed.description = f"Thank you for reporting `{str(member)}` for `{reason}`"
        thx_embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)

        embed = discord.Embed(title=f"Report", timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Reported Member", value=f"{member.mention} ({member.id})", inline=False)
        embed.add_field(name="Reporter", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)

        try:
            await ctx.author.send(embed=thx_embed)
        except discord.Forbidden:
            await ctx.send(embed=thx_embed, delete_after=10)

        await self.report_channel.send(embed=embed)
