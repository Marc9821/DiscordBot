from dotenv.main import load_dotenv; load_dotenv()
from discord.ext import commands
import os

bot = commands.Bot(command_prefix=".")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py") and filename != "__init__.py":
        bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print('I am online as {0.user}'.format(bot))

bot.run(os.getenv('DISCORD_BOT_TOKEN'))