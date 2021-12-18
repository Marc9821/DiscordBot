from discord.ext.commands.errors import MissingRequiredArgument
from utils import get_txt, write_txt, get_reddit, check_sub
from discord.ext import commands, tasks
import datetime
import discord


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subreddits_stats = get_txt()
        self.fetch_reddit.start()
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("A parameter is missing") 
    
    @commands.command(brief="subscribe subreddit", description="Use this command to subscribe to subreddits, provide the subreddit name and the \
channel name you want to receive the updates (if no channel name is given, the channel you send the command in will be used)")
    async def rsubscribe(self, ctx, sub, channel_name=None):
        exists = await check_sub(sub)
        if sub in self.subreddits_stats:
            await ctx.send("Already subscribed to this subreddit, did you mean to unsubscribe? To unsubscribe use .runsubscribe!")
            return
        elif exists == False:
            await ctx.send("No subreddit with that name found!")
            return
        else:
            if not channel_name:
                channel_name = ctx.message.channel.name
            channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            channel_id = channel.id
            self.subreddits_stats[sub] = {'children': [{'id': 'placeholder', 'utc': 1.0}], 'channel_id': channel_id, 'run': False}
            write_txt(self.subreddits_stats)
            for sub in self.subreddits_stats:
                await ctx.send(f'{sub} - {self.subreddits_stats[sub]["channel_id"]}')
            
    @commands.command(brief="unsubscribe subreddit", description="Use this command to unsubscribe to subreddits, only provide the subreddit name")
    async def runsubscribe(self, ctx, sub):
        if sub in self.subreddits_stats:
            del self.subreddits_stats[sub]
            write_txt(self.subreddits_stats)
            await ctx.send(f'Succesfully unsubscribed from **{sub}**')
            for sub in self.subreddits_stats:
                await ctx.send(f'{sub} - {self.subreddits_stats[sub]["channel_id"]}')
        else:
            await ctx.send("Subreddit is not subscribed, did you mean to subscribe? To subscribe use .rsubscribe!")
            return

    @commands.command(brief="list all subreddits", description="Lists all subscribed subreddits, only use the command, no keywords")
    async def rlist(self, ctx):
        for sub in self.subreddits_stats:
            await ctx.send(f'{sub} - {self.subreddits_stats[sub]["channel_id"]}')
    
    @tasks.loop(seconds=300)
    async def fetch_reddit(self):
        
        try:
            subs = [sub for sub in self.subreddits_stats.keys()]
            channel_ids = [channel_id['channel_id'] for channel_id in self.subreddits_stats.values()]
            await get_reddit(self, subs, channel_ids)
        except Exception as e:
            print(datetime.datetime.now())
            print(e)
    
def setup(bot):
    bot.add_cog(Reddit(bot))
    