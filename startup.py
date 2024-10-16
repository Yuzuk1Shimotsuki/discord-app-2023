import discord
import asyncio
import nest_asyncio
import os
import sys
import logging
import psutil
import signal
import subprocess
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded, ExtensionNotLoaded, NoEntryPointError, ExtensionFailed
from datetime import datetime
from quart import Quart
from dotenv import load_dotenv
from errorhandling.ErrorHandling import *

load_dotenv()
nest_asyncio.apply()
app = Quart("DiscordBot")
extensions = []
extensions_folders = ['general', 'moderation', 'errorhandling']

logger = logging.getLogger(__name__)
ConsoleOutputHandler = logging.StreamHandler()
logger.addHandler(ConsoleOutputHandler)
logging.basicConfig(filename='bot.log', level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Default configuration
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents, 
            command_prefix="!",
            self_bot=False,     # This is IMPORTANT!
            strip_after_prefix = True
        )

class MyNewHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page)
            await destination.send(embed=emby)

bot = Bot()
bot.help_command = MyNewHelp()

# Getting all extensions
def get_extensions():
    global extensions
    global extensions_folders
    extensions = []
    for folder in extensions_folders:
        for filename in os.listdir(f"./{folder}"):
            if filename.endswith('.py'):
                extensions.append(f'{folder}.{filename[:-3]}')
    return extensions

# Startup info
@bot.event
async def on_ready():
    logger.info("-" * 140)
    logger.info("Welcome to use the bot.")
    logger.info(f"Bot Username: {bot.user.name} #{bot.user.discriminator}")
    logger.info(f"Bot ID: {bot.application_id}")
    logger.info("-" * 140)
    logger.info("The bot is now initiated and ready for use!")
    logger.info("-" * 140)

# Sync all cogs for latest changes
@bot.command()
async def sync(ctx):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    synced = await bot.tree.sync()
    msg = await ctx.reply(f"Synced {len(synced)} command(s).")
    await asyncio.sleep(5)
    await msg.delete()
    await ctx.message.delete()

# Load cogs manually
@bot.command()
async def load(ctx, cog_name):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    # Front check if the cog was in the valid cog list or not
    extensions = get_extensions()
    if cog_name not in extensions:
        return await ctx.reply(ExtensionNotFoundError(cog=cog_name))
    try:
        await bot.load_extension(cog_name)
        await bot.tree.sync()
        msg = await ctx.reply(f"Cog `{cog_name}` has been loaded.")
        await asyncio.sleep(1)
        await msg.delete()
        await ctx.message.delete()
    except ExtensionAlreadyLoaded:
        return await ctx.reply(f"Cog `{cog_name}` has been already loaded!")
    except NoEntryPointError:
        return await ctx.reply(ReturnNoEntryPointError(cog=cog_name))
    except ExtensionFailed:
        return await ctx.reply(ExtensionFailedError(cog=cog_name))

# Unload cogs manually
@bot.command()
async def unload(ctx, cog_name):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    extensions = get_extensions()
    if cog_name not in extensions:
        # Front check if the cog was in the valid cog list or not
        return await ctx.reply(ExtensionNotFoundError(cog=cog_name))
    try:
        await bot.unload_extension(cog_name)
        await bot.tree.sync()
        msg = await ctx.reply(f"Cog `{cog_name}` has been unloaded.")
        await asyncio.sleep(2)
        await msg.delete()
        await ctx.message.delete()
    except ExtensionNotLoaded:
        return await ctx.reply(f"Cog `{cog_name}` has been already unloaded!")
    except NoEntryPointError:
        return await ctx.reply(ReturnNoEntryPointError(cog=cog_name))
    except ExtensionFailed:
        return await ctx.reply(ExtensionFailedError(cog=cog_name))

# Reload cogs manually
@bot.command()
async def reload(ctx, cog_name):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    extensions = get_extensions()
    if cog_name not in extensions:
        return await ctx.reply(ExtensionNotFoundError(cog=cog_name))
    try:
        await bot.reload_extension(cog_name)
        await bot.tree.sync()
        msg = await ctx.reply(f"Cog `{cog_name}` has been reloaded.")
        await asyncio.sleep(2)
        await msg.delete()
        await ctx.message.delete()
    except ExtensionNotLoaded:
        return await ctx.send(f"Cog `{cog_name}` has not been loaded.")
    except NoEntryPointError:
        return await ctx.reply(ReturnNoEntryPointError(cog=cog_name))
    except ExtensionFailed:
        return await ctx.reply(ExtensionFailedError(cog=cog_name))

# Retrieving system info from the bot
@bot.command()
async def systeminfo(ctx):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    # CPU
    cpuPercentage = psutil.cpu_percent(interval=1, percpu=False) * 100
    numberOfSystemCores = psutil.cpu_count(logical=False)
    numberOfLogicalCores = psutil.cpu_count(logical=True)
    # Memory
    ram = psutil.virtual_memory()
    usedRamInGB = round(ram.used / 1024 ** 3, 2)
    freeRamInGB = round(ram.free / 1024 ** 3, 2)
    totalRamInGB = round(ram.total / 1024 ** 3, 2)
    ramPercentage = ram.percent
    # Storage
    disk = psutil.disk_usage('/')
    usedVolumeInGB = round(disk.used / 1024 ** 3, 2)
    freeVolumeInGB = round(disk.free / 1024 ** 3, 2)
    totalVolumeInGB = round(disk.total / 1024 ** 3, 2)
    diskPercentage = disk.percent
    # Network
    network = psutil.net_io_counters()
    # Returning system info as embed
    hardware_info_embed = discord.Embed(title="Resource Usage (For reference only):", description='\u200b', timestamp=datetime.now(), color=ctx.author.colour)
    hardware_info_embed.add_field(name="CPU", value=f"CPU utilization: {cpuPercentage}%\nNumber of system cores: {numberOfSystemCores}\nNumber of logical cores: {numberOfLogicalCores}", inline=False)
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    hardware_info_embed.add_field(name="RAM", value=f"Memory in use: {usedRamInGB} / {totalRamInGB} GB ({ramPercentage}%)\nAvailible memory: {freeRamInGB} GB", inline=False)
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    hardware_info_embed.add_field(name="Storage", value=f"Space used: {usedVolumeInGB} / {totalVolumeInGB} GB ({diskPercentage}%)\nAvailible space: {freeVolumeInGB} GB", inline=False)
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    hardware_info_embed.add_field(name="Network", value=f"Number of bytes sent: {network.bytes_sent}\nNumber of bytes received: {network.bytes_recv}\nNumber of packets sent: {network.packets_sent}\nNumber of packets received: {network.packets_recv}\nTotal number of errors while receiving: {network.errin}\nTotal number of errors while sending: {network.errout}\nTotal number of incoming packets dropped: {network.dropin}\nTotal number of outgoing packets dropped: {network.dropout}", inline=False)
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    await ctx.reply(embed=hardware_info_embed)

# Restart the bot (Use it only as a LAST RESORT)
@bot.command()
async def restart(ctx):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    bot.clear()
    await bot.close()
    # Restart
    subprocess.Popen([sys.executable, *sys.argv])

# Shut down the bot (SELF DESTRUCT)
@bot.command()
async def shutdown(ctx):
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    bot.clear()
    await bot.close()
    exit(0)

# Load extensions
async def load_extensions():
    logger.info("\nGetting extensions...\n")
    initial_extensions = get_extensions()
    logger.info("\nLoading extensions...\n")
    for extension in initial_extensions:
        await bot.load_extension(extension)
        logger.info(extension)

# Starting the bot
@app.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    try:
        token = os.getenv("DISCORD_BOT_TOKEN") or ""
        if token == "":
            logger.error("No vaild tokens were found in the environment variable. Please add your token to the Secrets pane.")
            exit(1)
        asyncio.run(load_extensions())
        await bot.run(token)
    except discord.HTTPException as http_error:
        if http_error.status == 429:
            logger.error("\nThe Discord servers denied the connection for making too many requests, restarting in 7 seconds...")
            logger.error("\nIf the restart fails, get help from 'https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests'")
            subprocess.run(["python", "restarter.py"])
            os.kill(os.getpid(), signal.SIGINT)
        else:
            raise http_error
    except discord.errors.LoginFailure as token_error:
        logger.error(f"Cannot login to the bot at this point due to the following error: {token_error}\nPlease check your token and try again.")
        exit(1)


# ----------<Quart app>----------

# Returning the status of the Quart app
@app.route("/")
async def hello_world():
    return "Your application is now hosting normally."

# Actions after shutting down the Quart app (Ctrl + C)
@app.after_serving
async def my_shutdown():
    await bot.close()
    print("Shuting down...")
    os.kill(os.getpid(), signal.SIGINT)

# ----------</Quart app>----------



# Runs the whole application (Bot + Quart)
if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 8080)))  # PORT NUMBER: 8080 for Google Cloud Run
