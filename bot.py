from discord.ext.commands.errors import MissingRequiredArgument
from discord.ext import commands, tasks
from dotenv import load_dotenv
from itertools import cycle
import asyncpraw
import datetime
import requests
import discord
import random
import ast
import os


load_dotenv()
client = commands.Bot(command_prefix='.') #set the command prefix of the discord bot

def get_txt(): #on restart, load the last saved subreddits_status.txt dictionary file
    with open('DiscordBot/subreddits_stats.txt', 'r') as f:
        s = f.read().replace(" ","") #read string and replace all spaces
        subreddits = ast.literal_eval(s) #convert to dictionary
    
    return subreddits

subreddits_stats = get_txt()

@client.event
async def on_ready():
    change_status.start() #on discord bot ready, start the loop
    print('I am online as {0.user}'.format(client)) #log start to console

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, MissingRequiredArgument): #error handling for missing required arguments, send message
        await ctx.send("A parameter is missing") 

@client.command()
async def rsubscribe(ctx, sub, channel_name): #add new subreddit to subscribed subreddits
    if sub in subreddits_stats: #check if subreddit already subscribed
        await ctx.send("Already subscribed to this subreddit, did you mean to unsubscribe? To unsubscribe use .runsubscribe!")
        return
    else:
        channel = discord.utils.get(ctx.guild.channels, name=channel_name) #get discord channel id from channel name
        channel_id = channel.id
        subreddits_stats[sub] = {'children': [{'id': 'placeholder', 'utc': 1.0}], 'channel_id': channel_id, 'run': False} #add subreddit to subreddits_status dictionary
        write_txt(subreddits_stats) #update subreddits_status.txt file
        for sub in subreddits_stats:
            await ctx.send(f'{sub} - {subreddits_stats[sub]["channel_id"]}') #send message for each subreddit and the corresponding discord channel

@client.command()
async def runsubscribe(ctx, sub): #remove subreddit from subscribed subreddits
    if sub in subreddits_stats: #check if subreddit is subscribed
        del subreddits_stats[sub] #delete subreddit
        write_txt(subreddits_stats) #update subreddits_status.txt file
        for sub in subreddits_stats:
            await ctx.send(f'{sub} - {subreddits_stats[sub]["channel_id"]}') #send message for each subreddit and the corresponding discord channel
    else: #subreddit not subscribed, send message
        await ctx.send("Subreddit is not subscribed, did you mean to subscribe? To subscribe use .rsubscribe!")
        return
        
@client.command()
async def rlist(ctx): #send message for each subscribed subreddit and the corresponding discord channel
    for sub in subreddits_stats:
        await ctx.send(f'{sub} - {subreddits_stats[sub]["channel_id"]}')
        
@client.command()
async def p(ctx, keyword, n=5): #get image from image board, keyword has to be specified, number of images set to 5 if not specified
    if n >= 20: #limit number of images to 19
        ctx.send('Not more than 19 please!')
    response = requests.get(url=f'https://api.{os.getenv("API_CONNECTOR_ONE")}//index.php?page=dapi&s=post&q=index&limit=250&json=1&tags={keyword}') #connect to api and get results
    try:
        json_data = response.json() #convert results to json
    except:
        await ctx.send('Found nothing!') #no results found or api down, send message
        return
    
    for i in range(n): #loop the specified amount of times
        v = random.randint(0,249) #get random integer from number of images received from api
        embed = discord.Embed(title=f'{os.getenv("API_CONNECTOR_ONE")} - {keyword}', color=0x00a8a5) #create embed, title and color
        embed.set_author(name="Ana V2", icon_url='https://i.imgur.com/fa1HOOn.jpg') #set author
        embed.set_image(url=f'{json_data[v]["file_url"]}') #set image
        await ctx.send(embed=embed) #send embed

@client.command()
async def clear(ctx, amount=5): #delete a specified amount of posts in current channel
    await ctx.channel.purge(limit=amount)

status = cycle(['Reddit', 'Twitch'])
@tasks.loop(seconds=300) #set loop repeat timer
async def change_status(): #start loop
    
    try: #try catch if failed to establish connection with asyncpraw
        for sub in subreddits_stats.keys(): #go through all subscribed subreddits
            channel_id = subreddits_stats[sub]['channel_id'] #get channel id where to post current subreddit
            new_posts = await get_reddit(sub) #get all new posts from subreddit
            await send_updates(new_posts, channel_id, sub) #send updates in channel
    except Exception as e:
        print(datetime.datetime.now())
        print(e)
        
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=next(status))) #change bot status


async def get_reddit(sub):
    reddit = asyncpraw.Reddit( #establish connection with asyncpraw
        client_id = os.getenv('REDDIT_CLIENT_ID'), #get information from .env
        client_secret = os.getenv('REDDIT_CLIENT_SECRET'), #get information from .env
        user_agent = os.getenv('REDDIT_USERAGENT'), #get information from .env
    )

    new_posts = [] #save new posts
    lim = 25 #set limit of how many posts to get per request, max 100
    subreddit = await reddit.subreddit(sub, fetch=True) #fetch subreddit

    async for submission in subreddit.new(limit=lim):
        try:
            author = submission.author.name #set author name
        except:
            author = submission.author #set author name in case of crosspost
        title = submission.title #set title
        post_url = 'https://www.reddit.com' + submission.permalink #create url to post
        post_id = submission.id #set unique id
        utc = submission.created_utc #set utc
        image_url = submission.url #set image url
        
        new_posts.append([author, title, post_url, utc, image_url, post_id]) #add information to list
        
    await reddit.close() #close reddit connection
    
    id_list = [child['id'] for child in subreddits_stats[sub]['children']] #get all id's from subreddits_status of corresponding sub
    time_list = [child['utc'] for child in subreddits_stats[sub]['children']] #get all utc's from subreddits_status of corresponding sub
    newest_time = max(time_list) #get highest value, e.g. the newest time
    
    if subreddits_stats[sub]['run'] == False: #for first run delete placeholder values
        subreddits_stats[sub]['run'] = True
        subreddits_stats[sub]['children'].pop()
    
    new_posts.reverse() #reverse post order, since the newest was the first
    to_post = []
    for post in new_posts: #go through all posts
        if post[5] in id_list: #if id of current post is in id_list then skip since it has been posted already
            continue
        elif post[3] >= newest_time: #double check to not allow old posts in case a new post gets deleted
            subreddits_stats[sub]['children'].append({'id': post[5], 'utc': post[3]}) #append current post to subreddits_status
            to_post.append(post) #append to to_post list
            if len(subreddits_stats[sub]['children']) > lim: #remove oldest entry if a new one is created
                subreddits_stats[sub]['children'].pop(0)

    write_txt(subreddits_stats) #update subreddits_status.txt file
    return to_post #return list of posts that have to be posted

async def send_updates(new_posts, channel_id, sub):
    for new_post in new_posts: #for every post create an embed
        embed = discord.Embed(title=f'{new_post[1]} - {sub}', color=0xff0000)
        embed.set_author(name="Ana V2", icon_url='https://i.imgur.com/fa1HOOn.jpg')
        embed.add_field(name="Post URL", value=new_post[2], inline=False)
        embed.set_image(url=f'{new_post[4]}')
        embed.set_footer(text=f'{datetime.datetime.fromtimestamp(new_post[3])} | by /u/{new_post[0]}')
        channel = client.get_channel(channel_id)
        await channel.send(embed=embed) #send embed
    return

def write_txt(file): #update subreddits_status.txt file
    with open('DiscordBot/subreddits_stats.txt', 'w') as f:
        f.write(str(file))

client.run(os.getenv('DISCORD_TOKEN')) #connect bot to discord, token is saved in .env
