from discord.ext import commands, tasks


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.listening.start()
        
    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Pong!")
        
def setup(bot):
    bot.add_cog(Basic(bot))