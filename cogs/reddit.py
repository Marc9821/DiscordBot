from discord.ext.commands.errors import MissingRequiredArgument
from discord.ext import commands, tasks
import asyncpraw
import datetime
import discord
import ast
import os


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subreddits_stats = get_txt()
        self.fetch_reddit.start()
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("A parameter is missing") 
    
    @commands.command(brief="subscribe subreddit", description="Use this command to subscribe to subreddits, provide the subreddit name and the channel name you want to receive the updates")
    async def rsubscribe(self, ctx, sub, channel_name):
        if sub in self.subreddits_stats:
            await ctx.send("Already subscribed to this subreddit, did you mean to unsubscribe? To unsubscribe use .runsubscribe!")
            return
        else:
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
            for sub in self.subreddits_stats.keys():
                channel_id = self.subreddits_stats[sub]['channel_id']
                new_posts = await get_reddit(self, sub)
                await send_updates(self, new_posts, channel_id, sub)
        except Exception as e:
            print(datetime.datetime.now())
            print(e)
    




def setup(bot):
    bot.add_cog(Reddit(bot))
    
async def get_reddit(self, sub):
    reddit = asyncpraw.Reddit(
        client_id = os.getenv('REDDIT_CLIENT_ID'),
        client_secret = os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent = os.getenv('REDDIT_USERAGENT'),
    )

    new_posts = []
    lim = 25
    subreddit = await reddit.subreddit(sub, fetch=True)

    async for submission in subreddit.new(limit=lim):
        try:
            author = submission.author.name
        except:
            author = submission.author
        title = submission.title
        post_url = 'https://www.reddit.com' + submission.permalink
        post_id = submission.id
        utc = submission.created_utc
        image_url = submission.url
        
        new_posts.append([author, title, post_url, utc, image_url, post_id])
        
    await reddit.close()
    
    id_list = [child['id'] for child in self.subreddits_stats[sub]['children']]
    time_list = [child['utc'] for child in self.subreddits_stats[sub]['children']]
    newest_time = max(time_list)
    
    if self.subreddits_stats[sub]['run'] == False:
        self.subreddits_stats[sub]['run'] = True
        self.subreddits_stats[sub]['children'].pop()
    
    new_posts.reverse()
    to_post = []
    for post in new_posts:
        if post[5] in id_list:
            continue
        elif post[3] >= newest_time:
            self.subreddits_stats[sub]['children'].append({'id': post[5], 'utc': post[3]})
            to_post.append(post)
            if len(self.subreddits_stats[sub]['children']) > lim:
                self.subreddits_stats[sub]['children'].pop(0)

    write_txt(self.subreddits_stats)
    return to_post

async def send_updates(self, new_posts, channel_id, sub):
    for new_post in new_posts:
        embed = discord.Embed(title=f'{new_post[1]} - {sub}', color=0xff0000)
        embed.set_author(name="Ana V2", icon_url='https://i.imgur.com/fa1HOOn.jpg')
        embed.add_field(name="Post URL", value=new_post[2], inline=False)
        embed.set_image(url=f'{new_post[4]}')
        embed.set_footer(text=f'{datetime.datetime.fromtimestamp(new_post[3])} | by /u/{new_post[0]}')
        channel = self.bot.get_channel(channel_id)
        await channel.send(embed=embed)
    return    

def get_txt():
    with open('subreddits_stats.txt', 'r') as f:
        s = f.read().replace(" ","")
        subreddits = ast.literal_eval(s)
    
    return subreddits

def write_txt(file):
    with open('subreddits_stats.txt', 'w') as f:
        f.write(str(file))
