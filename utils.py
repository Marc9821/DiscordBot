import asyncprawcore
import datetime
import discord
import time
import ast


async def get_reddit(self, subs, channel_ids):
    for (sub, channel_id) in zip(subs, channel_ids):    
        new_posts = []
        lim = 10
        subreddit = await self.reddit.subreddit(sub, fetch=True)
        start = datetime.datetime.now()

        async for submission in subreddit.new(limit=lim):
            try:
                author = submission.author.name
            except:
                author = submission.author
            title = submission.title
            if len(title) > 220:
                title = title[:220]
            post_url = 'https://www.reddit.com' + submission.permalink
            post_id = submission.id
            utc = submission.created_utc
            url = submission.url
            thumbnail_url = submission.thumbnail
            try:
                preview_url = submission.preview['images'][0]['source']['url']
            except:
                preview_url = False
                
            if preview_url:
                image_url = preview_url
            elif thumbnail_url.endswith(('.jpg', '.png', '.jpeg')):
                image_url = thumbnail_url
            else:
                image_url = url
            
            new_posts.append([author, title, post_url, utc, image_url, post_id])
        
        id_list = [child['id'] for child in self.subreddits_stats[sub]['children']]
        time_list = [child['utc'] for child in self.subreddits_stats[sub]['children']]
        newest_time = max(time_list)
        
        if self.subreddits_stats[sub]['run'] == False:
            self.subreddits_stats[sub]['run'] = True
            self.subreddits_stats[sub]['children'].pop()
        
        to_post = []
        for post in reversed(new_posts):
            if post[5] in id_list:
                continue
            elif post[3] >= newest_time:
                self.subreddits_stats[sub]['children'].append({'id': post[5], 'utc': post[3]})
                to_post.append(post)
                while len(self.subreddits_stats[sub]['children']) > lim:
                    self.subreddits_stats[sub]['children'].pop(0)

        if to_post:
            await send_updates(self, to_post, channel_id, sub)
        end = datetime.datetime.now()
        delta = end - start
        delta_s = 2 - delta.total_seconds()
        time.sleep(max(0,delta_s))
    
    write_txt(self.subreddits_stats)
    return

async def send_updates(self, new_posts, channel_id, sub):
    for new_post in new_posts:
        embed = discord.Embed(title=f'{new_post[1]} - {sub}', color=0xff0000)
        embed.set_author(name="Ana V2", icon_url='https://i.imgur.com/fa1HOOn.jpg')
        embed.add_field(name="Post URL", value=new_post[2], inline=False)
        if new_post[4].startswith('http'):
            embed.set_image(url=f'{new_post[4]}')
        embed.set_footer(text=f'{datetime.datetime.fromtimestamp(new_post[3])} | by /u/{new_post[0]}')
        channel = self.bot.get_channel(channel_id)
        await channel.send(embed=embed)
    return  

async def check_sub(self, sub):
    exists = True
    try:
        await self.reddit.subreddit(sub, fetch=True)
    except asyncprawcore.Redirect:
        exists = False
    return exists

async def send_subreddit_list(self, ctx):
    subreddits = []
    for sub in self.subreddits_stats:
        subreddits.append(f'**{sub}** - {self.subreddits_stats[sub]["channel_name"]}')
    embed=discord.Embed(title="Subscribed subreddits:", description = "\n".join(subreddits))
    embed.set_author(name="Ana V2", icon_url="https://i.imgur.com/fa1HOOn.jpg")
    await ctx.send(embed=embed)

def get_txt():
    with open('subreddits_stats.txt', 'r') as f:
        s = f.read().replace(" ","")
        subreddits = ast.literal_eval(s)
    
    return subreddits

def write_txt(file):
    with open('subreddits_stats.txt', 'w') as f:
        f.write(str(file))
        