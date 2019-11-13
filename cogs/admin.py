from discord.ext import commands
import discord

import asyncio


class Administration(commands.Cog):
    """Only work in a guild"""
    def __init__(self, bot):
        self.bot = bot
        self.delete_after = 5.0

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False

        return self.bot.is_admin(ctx.author)

    async def cleanup(self, ctx, msg):
        await asyncio.sleep(self.delete_after)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        else:
            if msg:
                await msg.delete()

    @commands.command()
    async def load(self, ctx, cog: str):
        """Loads cog"""
        msg = None
        try:
            self.bot.load_extension('cogs.' + cog)
        except Exception as e:
            await ctx.send(e)
        else:
            msg = await ctx.send(f"`cogs.{cog}` loaded")
        finally:
            await self.cleanup(ctx, msg)

    @commands.command()
    async def unload(self, ctx, cog: str):
        """Unloads cog"""
        if cog != 'admin':
            msg = None
            try:
                self.bot.unload_extension('cogs.' + cog)
            except Exception as e:
                await ctx.send(e)
            else:
                msg = await ctx.send(f"`cogs.{cog}` unloaded")
            finally:
                await self.cleanup(ctx, msg)
        else:
            await ctx.send('Cannot unload that cog.')

    @commands.command()
    async def reload(self, ctx, cog: str):
        """Reloads cog"""
        msg = None
        try:
            self.bot.reload_extension('cogs.' + cog)
        except Exception as e:
            await ctx.send(e)
        else:
            msg = await ctx.send(f"`cogs.{cog}` reloaded")
        finally:
            await self.cleanup(ctx, msg)


def setup(bot):
    bot.add_cog(Administration(bot))
