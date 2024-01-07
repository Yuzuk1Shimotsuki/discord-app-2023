import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

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

# Load extensions
def load_extensions():
    initial_extensions = []
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            initial_extensions.append(f"cogs.{filename[:-3]}")
    print("\nLoading extensions...\n")
    print(initial_extensions)
    for extension in initial_extensions:
        bot.load_extension(extension)
    print("\nEstablishing connection...\n")


if __name__ == "__main__":
    load_extensions()

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
