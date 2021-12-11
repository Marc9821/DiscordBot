from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(brief="delete posts", description="delete a specified number of posts")
    async def clear(self, ctx, amount=5):
        await ctx.channel.purge(limit=amount)
        
def setup(bot):
    bot.add_cog(Admin(bot))