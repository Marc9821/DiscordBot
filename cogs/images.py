from discord.ext import commands
import requests
import discord
import random
import os


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(brief="get random images", description="get random images, specifiy keyword for image and number of images, max is 19")
    async def p(self, ctx, keyword, n=5):
        if n >= 20:
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
        
def setup(bot):
    bot.add_cog(Images(bot))