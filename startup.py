# This example requires the 'message_content' intent.

import discord
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents, 
            command_prefix="?", 
            self_bot=False, strip_after_prefix = True
        )

bot = Bot()


# Startup
@bot.event
async def on_ready():
    print("-" * 65)
    print("Welcome to use the bot.")
    print(f"Bot Username: {bot.user.name} #{bot.user.discriminator}")
    print(f"Bot ID: {bot.application_id}")
    print("-" * 65)
    print("The bot is now ready for use!")
    print("-" * 65)

@bot.command(name="sync") 
async def sync(ctx):
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")

# Load extensions
async def load_extensions():
    print("\nLoading extensions...\n")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'cogs.{filename[:-3]}')

if __name__ == "__main__":
    asyncio.run(load_extensions())

for commands in bot.tree.walk_commands():
    print(commands.name)

# Runs the bot
try:
    token = os.getenv("DISCORD_BOT_TOKEN") or ""
    if token == "":
        raise Exception("Please add your token to the Secrets pane.")
    bot.run(token)
except discord.HTTPException as http_error:
    if http_error.status == 429:
        print("\nThe Discord servers denied the connection for making too many requests, restarting in 7 seconds...")
        print("\nIf the restart fails, get help from 'https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests'")
        os.system("python restarter.py")
        os.system("kill 1")
    else:
        raise http_error
except discord.errors.LoginFailure as token_error:
    print(f"Cannot login to the bot at this point due to the following error: {token_error}\nPlease check your token and try again.")
    exit(1)
