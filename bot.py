import asyncpraw
import datetime
import requests
import discord
import random
import ast
import os
from discord.ext import commands, tasks
from discord.ext.commands.errors import MissingRequiredArgument
from itertools import cycle
from dotenv import load_dotenv


load_dotenv()
client = commands.Bot(command_prefix='.')

def get_txt():
    with open('subreddits_stats.txt', 'r') as f:
        s = f.read().replace(" ","")
        subreddits = ast.literal_eval(s)
    
    return subreddits

subreddits_stats = get_txt()

@client.event
async def on_ready():
    print(subreddits_stats)
    change_status.start()
    print('I am online as {0.user}'.format(client))

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        await ctx.send("A parameter is missing") 

@client.command()
async def rsubscribe(ctx, sub, channel_name):
    if sub in subreddits_stats:
        await ctx.send("Already subscribed to this subreddit, did you mean to unsubscribe? To unsubscribe use .runsubscribe!")
        return
    else:
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)
        channel_id = channel.id
        subreddits_stats[sub] = {'children': [{'id': 'placeholder', 'utc': 1.0}], 'channel_id': channel_id, 'run': False}
        for sub in subreddits_stats:
            await ctx.send(f'{sub} - {subreddits_stats[sub]["channel_id"]}')

@client.command()
async def runsubscribe(ctx, sub):
    if sub in subreddits_stats:
        del subreddits_stats[sub]
        for sub in subreddits_stats:
            await ctx.send(f'{sub} - {subreddits_stats[sub]["channel_id"]}') 
    else:
        await ctx.send("Subreddit is not subscribed, did you mean to subscribe? To subscribe use .rsubscribe!")
        return
        
@client.command()
async def rlist(ctx):
    for sub in subreddits_stats:
        await ctx.send(f'{sub} - {subreddits_stats[sub]["channel_id"]}')
        
@client.command()
async def p(ctx, keyword, n=5):
    if n >= 20:
        ctx.send('Not more than 19 please!')
    response = requests.get(url=f'https://api.{os.getenv("API_CONNECTOR_ONE")}//index.php?page=dapi&s=post&q=index&limit=250&json=1&tags={keyword}')
    try:
        json_data = response.json()
    except:
        await ctx.send('Found nothing!')
        return
    
    for i in range(n):
        v = random.randint(0,249)
        embed = discord.Embed(title=f'{os.getenv("API_CONNECTOR_ONE")} - {keyword}', color=0x00a8a5)
        embed.set_author(name="Ana V2", icon_url='https://i.imgur.com/fa1HOOn.jpg')
        embed.set_image(url=f'{json_data[v]["file_url"]}')
        await ctx.send(embed=embed)

@client.command()
async def clear(ctx, amount=5):
    await ctx.channel.purge(limit=amount)

status = cycle(['Reddit', 'Twitch'])
@tasks.loop(seconds=300)
async def change_status():
    
    try:
        for sub in subreddits_stats.keys():
            channel_id = subreddits_stats[sub]['channel_id']
            new_posts = await get_reddit(sub)
            stat = await send_updates(new_posts, channel_id, sub)
            print(f'{stat} with {sub}')
    except Exception as e:
        print(e)
        
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=next(status)))


async def get_reddit(sub):
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
    
    id_list = [child['id'] for child in subreddits_stats[sub]['children']]
    time_list = [child['utc'] for child in subreddits_stats[sub]['children']]
    newest_time = max(time_list)
    
    if subreddits_stats[sub]['run'] == False:
        subreddits_stats[sub]['run'] = True
        subreddits_stats[sub]['children'].pop()
    
    new_posts.reverse()
    to_post = []
    for post in new_posts:
        if post[5] in id_list:
            continue
        elif post[3] >= newest_time:
            subreddits_stats[sub]['children'].append({'id': post[5], 'utc': post[3]})
            to_post.append(post)
            if len(subreddits_stats[sub]['children']) > lim:
                subreddits_stats[sub]['children'].pop(0)

    write_txt(subreddits_stats)
    return to_post

async def send_updates(new_posts, channel_id, sub):
    for new_post in new_posts:
        embed = discord.Embed(title=f'{new_post[1]} - {sub}', color=0xff0000)
        embed.set_author(name="Ana V2", icon_url='https://i.imgur.com/fa1HOOn.jpg')
        embed.add_field(name="Post URL", value=new_post[2], inline=False)
        embed.set_image(url=f'{new_post[4]}')
        embed.set_footer(text=f'{datetime.datetime.fromtimestamp(new_post[3])} | by /u/{new_post[0]}')
        channel = client.get_channel(channel_id)
        await channel.send(embed=embed)
    return 'done'

def write_txt(file):
    with open('subreddits_stats.txt', 'w') as f:
        f.write(str(file))

client.run(os.getenv('DISCORD_TOKEN'))
