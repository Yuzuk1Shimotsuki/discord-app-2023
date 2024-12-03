import discord
import asyncio
import netifaces
import nest_asyncio
import os
import sys
import logging
import psutil
import signal
import socket
import subprocess
import time
from multiprocessing import Process, Queue
from GetDetailIPv4Info import *
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded, ExtensionNotLoaded, NoEntryPointError, ExtensionFailed
from datetime import datetime
from quart import Quart
from dotenv import load_dotenv
from configs.Logging import setup_logger
from errorhandling.ErrorHandling import *

load_dotenv()
nest_asyncio.apply()
app = Quart("DiscordBot")
extensions = []
extensions_folders = ['general', 'moderation', 'errorhandling', 'configs']

logger = setup_logger('discord_bot', 'bot.log', logging.INFO)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


instruction_queue = None    # IMPORTANT for multiprocessing


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
            embed = discord.Embed(description=page)
            await destination.send(embed=embed)

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
                extension = f'{folder}.{filename[:-3]}'

                if extension == "general.ChatGPT" and os.getenv("ENABLE_AI") == "False":
                    continue

                if extension == "general.MusicPlayer" and os.getenv("ENABLE_MUSIC") == "False":
                    continue

                extensions.append(extension)

    return extensions


# Startup info
@bot.event
async def on_ready():
    logger.info(
f'''

{"-" * 120}

Welcome to the application!

Bot Username: {bot.user.name}#{bot.user.discriminator}
Bot ID: {bot.application_id}

The application is now initialized and waiting for your demands!

{"-" * 120}

'''
        )


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
    
    def convert_to_GB(raw):
        return round(raw / 1024 ** 3, 2)
    # CPU
    cpuPercentage = psutil.cpu_percent()
    numberOfSystemCores = psutil.cpu_count(logical=False)
    numberOfLogicalCores = psutil.cpu_count(logical=True)

    # Memory
    ram = psutil.virtual_memory()
    usedRamInGB = convert_to_GB(ram.used)
    availableRamInGB = convert_to_GB(ram.available)
    totalRamInGB = convert_to_GB(ram.total)
    ramPercentage = ram.percent
    
    # Storage
    disk = psutil.disk_usage('/')
    usedVolumeInGB = convert_to_GB(disk.used)
    freeVolumeInGB = convert_to_GB(disk.free)
    totalVolumeInGB = convert_to_GB(disk.total)
    diskPercentage = disk.percent

    # Network
    hostname = socket.gethostname()
    ipInfo = GetDetailIPv4Info()
    network = psutil.net_io_counters()

    # Returning system info as embed
    hardware_info_embed = discord.Embed(title="Resource Usage (For reference only):", description='\u200b', timestamp=datetime.now(), color=ctx.author.colour)

    # CPU
    hardware_info_embed.add_field(name="CPU", value=f"CPU utilization: {cpuPercentage}%\nNumber of system cores: {numberOfSystemCores}\nNumber of logical cores: {numberOfLogicalCores}", inline=True)
    
    # Memory
    hardware_info_embed.add_field(name="RAM", value=f"Memory in use: {usedRamInGB} / {totalRamInGB} GB ({ramPercentage}%)\nAvailible memory: {availableRamInGB} GB", inline=True)
    hardware_info_embed.add_field(name="Storage", value=f"Space used: {usedVolumeInGB} / {totalVolumeInGB} GB ({diskPercentage}%)\nAvailible space: {freeVolumeInGB} GB", inline=True)
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    
    # Basic Network
    ip_addresses = [netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr'] for iface in netifaces.interfaces() if netifaces.AF_INET in netifaces.ifaddresses(iface)]
    subnets = [netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['netmask'] for iface in netifaces.interfaces() if netifaces.AF_INET in netifaces.ifaddresses(iface)]
    gateways = [netifaces.gateways()['default'][netifaces.AF_INET][0] for gateways in netifaces.interfaces() if "default" in netifaces.gateways()]
    
    try:
        hardware_info_embed.add_field(name="Network Information (Basic)", value=f"IPv4 Address(s): {ip_addresses}\nSubnet(s) Mask: {subnets}\nGateway(s): {gateways}", inline=True)
    
    except:
        pass
    
    # Advanced Network
    hardware_info_embed.add_field(name="Network Information (Advanced)", value=f"Hostname: {hostname}\nIPv4: {ipInfo.ip}\nIP Hostname: {ipInfo.hostname}\nCountry or district: {ipInfo.country}\nRegion: {ipInfo.region}\nCity: {ipInfo.city}\n Organization: {ipInfo.organization}\nPostal code: {ipInfo.postal}\nLocation: {ipInfo.location}", inline=True)
    
    # Packets transmission
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    hardware_info_embed.add_field(name="Packets transmission:", value=f"Number of bytes sent: {network.bytes_sent}\nNumber of bytes received: {network.bytes_recv}\nNumber of packets sent: {network.packets_sent}\nNumber of packets received: {network.packets_recv}\nTotal number of errors while receiving: {network.errin}\nTotal number of errors while sending: {network.errout}\nTotal number of incoming packets dropped: {network.dropin}\nTotal number of outgoing packets dropped: {network.dropout}", inline=False)
    hardware_info_embed.add_field(name="\u200b", value="", inline=False)
    
    await ctx.reply(embed=hardware_info_embed)


# Restart the bot (Use it only as a LAST RESORT)
@bot.command()
async def restart(ctx):
    global is_restarting
    is_restarting = True
    
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    bot.clear()
    await bot.close()
    await self_restart()


# Shut down the bot and the server (SELF DESTRUCT)
@bot.command()
async def shutdown(ctx):
    global is_shutdown
    is_shutdown = True
    
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    bot.clear()
    await bot.close()
    await app.shutdown()


# Load extensions
async def load_extensions():
    logger.info("\nGetting extensions...\n")
    initial_extensions = get_extensions()
    logger.info("\nLoading extensions...\n")
    
    for extension in initial_extensions:
        await bot.load_extension(extension)
        logger.info(extension)


# Start the bot application
async def start_bot():
    try:
        token = os.getenv("DISCORD_BOT_TOKEN") or ""
        
        if token == "":
            logger.error("No vaild tokens were found in the environment variable. Please add your token to the Secrets pane.")
            exit(1)
        
        asyncio.run(load_extensions())
        await bot.login(token)
        await bot.connect()
    
    except discord.HTTPException as http_error:
        if http_error.status == 429:
            logger.error("\nThe Discord servers denied the connection for making too many requests, restarting in 7 seconds...")
            logger.error("\nIf the restart fails, get help from 'https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests'")
            instruction_queue.put("restart")    # Put "restart" to the queue to restart the web server
        
        else:
            raise http_error
    
    except discord.errors.LoginFailure as token_error:
        logger.error(f"Cannot login to the bot at this point due to the following error: {token_error}\nPlease check your token and try again.")
        exit(1)


# ----------<Quart app>----------


# Coroutine called when the web server starts
@app.before_serving
async def before_serving():
    # Rewrite for database connection in the future
    app.add_background_task(start_bot)


@app.route("/")
def hello_world():
    return "Hello, World!"


# Returning the status of the Quart app
@app.get("/status")
def status():
    if len(app.background_tasks) == 0:
        return "No applications were hosting now."
    
    return "Your applications are now hosting normally."


@app.get('/restart')
async def self_restart():
    await bot.close()
    instruction_queue.put("restart")    # Put "restart" to the queue to restart the web server
    return "Please Wait. Your server is now restarting..."


# Actions after shutting down the Quart app (Ctrl + C)
@app.after_serving
async def self_shutdown():
    await bot.close()
    instruction_queue.put("shutdown")   # Put "shutdown" to the queue to terminate the web server


# ----------</Quart app>----------


# Runs the whole application (Bot + Quart)
def startup(queue):
    global instruction_queue
    instruction_queue = queue
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))  # Custom PORT: 3000 for Azure and Docker



if __name__ == "__main__":
    try:
        q = Queue() # IMPORTANT
        p = Process(target=startup, args=[q,])
        p.start()
        while q.empty():    # Waiting queue, sleep if there is no call
            time.sleep(0.001)   # Using minimal time delay to make it neglectable
        p.terminate()
        # Get instruction from the queue

        match q.get():
            case "shutdown":
                # Terminate the program
                print("Shutting down...")
                os.kill(os.getpid(), signal.SIGINT)

            case "restart" | "reboot":
                pass

            case _:
                raise ValueError("Invaild input for Queue, must be either 'shutdown', 'reboot' or 'restart'.")
            
        # Restart the program
        print("Please Wait. Your server is now restarting...")
        time.sleep(7)
        args = [sys.executable] + [sys.argv[0]]
        subprocess.call(args)

    except KeyboardInterrupt:
        print("Shutting down by Keyboard Interruption...")
        os.kill(os.getpid(), signal.SIGINT)


