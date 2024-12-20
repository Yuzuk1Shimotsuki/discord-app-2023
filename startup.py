import discord
import asyncio
import nest_asyncio
import psutil
import netifaces
import os
import sys
import logging
import socket
import subprocess
import motor.motor_asyncio as motor
from asyncio import sleep, Queue
from GetDetailIPv4Info import *
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded, ExtensionNotLoaded, NoEntryPointError, ExtensionFailed
from dotenv import load_dotenv
from datetime import datetime
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart
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
instruction_queue = None    # IMPORTANT 


class Bot(commands.Bot):
    """
    Default configuration
    """
    def __init__(self):
        super().__init__(
            intents=intents,
            command_prefix="?",
            self_bot=False,  # IMPORTANT!
            strip_after_prefix=True
        )
        self.mongo_client = None  # Initialize later in setup_hook


    async def setup_hook(self):
        self.mongo_client = motor.AsyncIOMotorClient(os.getenv("MONGO_DATABASE_URL"))   # Initialize the motor client here to ensure it's tied to the correct event loop

        try:
            # Self MongoDB connedction test
            await self.mongo_client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")

        except Exception as e:
            raise ConnectionError(f"Fatal: An error occurred while trying to connect to MongoDB cluster: {e}")

        # Load extensions
        await load_extensions()


    def get_cluster(self):
        """
        Retrive mongo database for all cogs
        """
        return self.mongo_client


    async def close_db(self):
        """
        This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

        Ensure the motor client is properly closed
        """
        if self.mongo_client:
            self.mongo_client.close()
        await super().close()


class MyNewHelp(commands.MinimalHelpCommand):
    """
    Custom Help UI (Pending to rewrite)
    """
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page)
            await destination.send(embed=embed)


bot = Bot()
bot.help_command = MyNewHelp()


async def load_extensions():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).
    
    Load extensions upon startup
    """
    logger.info("\nGetting extensions...\n")
    initial_extensions = await get_extensions()
    logger.info("\nLoading extensions...\n")
    
    for extension in initial_extensions:
        await bot.load_extension(extension)
        logger.info(extension)


async def get_extensions():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Getting all extensions
    """
    global extensions_folders
    extensions = []

    # Use asyncio.to_thread to perform blocking I/O in a separate thread
    for folder in extensions_folders:
        folder_path = f"./{folder}"
        if not os.path.exists(folder_path):
            continue

        filenames = await asyncio.to_thread(os.listdir, folder_path)

        for filename in filenames:
            if filename.endswith('.py'):
                extension = f'{folder}.{filename[:-3]}'

                if extension == "general.ChatGPT" and os.getenv("ENABLE_AI") == "False":
                    continue

                if extension == "general.MusicPlayer" and os.getenv("ENABLE_MUSIC") == "False":
                    continue

                extensions.append(extension)

    return extensions


@bot.event
async def on_ready():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Displaying startup info
    """
    logger.info(
f'''

{"-" * 120}

Welcome to the application!

Bot Username: {bot.user.name}#{bot.user.discriminator}
Bot ID: {bot.application_id}

The application is now initialized and waiting on your demands!

{"-" * 120}

'''
        )


@bot.command()
async def sync(ctx):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Sync all cogs for latest changes
    """
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    synced = await bot.tree.sync()
    msg = await ctx.reply(f"Synced {len(synced)} command(s).")

    await asyncio.sleep(5)
    await msg.delete()
    await ctx.message.delete()


@bot.command()
async def load(ctx, cog_name):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Load cogs manually
    """
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    extensions = get_extensions()
    if cog_name not in extensions:  # Front check if the cog was in the valid cog list or not
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
    

@bot.command()
async def unload(ctx, cog_name):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).
    
    Unload cogs manually
    """
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    extensions = get_extensions()

    if cog_name not in extensions:  # Front check if the cog was in the valid cog list or not
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
    


@bot.command()
async def reload(ctx, cog_name):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Reload cogs manually
    """
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


@bot.command()
async def systeminfo(ctx):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Retrieving system info from the bot
    """
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


@bot.command()
async def restart(ctx):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Restart the bot (Use it only as a LAST RESORT)
    """
    global is_restarting
    is_restarting = True
    
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    bot.clear()
    await bot.close()
    await self_restart()


@bot.command()
async def shutdown(ctx):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Shut down the bot and the server (SELF DESTRUCT)
    """
    global is_shutdown
    is_shutdown = True
    
    if not await bot.is_owner(ctx.author):
        return await ctx.reply(NotBotOwnerError())
    
    bot.clear()
    await bot.close()
    await app.shutdown()


async def start_bot():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Start the bot application
    """
    try:
        token = os.getenv("DISCORD_BOT_TOKEN") or ""
        
        if token == "":
            logger.error("No vaild tokens were found in the environment variable. Please add your token to the Secrets pane.")
            exit(1)

        await bot.start(token)
    
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


"""
The following code is the primary operational logic of the application.  
To optimize resource usage, multiprocessing has been replaced with asynchronous operations, which are more lightweight and efficient.  
However, as a trade-off, the shutdown process may take slightly longer due to the need for graceful task cancellation and cleanup.
"""


@app.before_serving
async def before_serving():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Called when the web server starts
    """
    app.add_background_task(start_bot)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.get("/status")
def status():
    """
    Returning the status of the Quart app
    """
    if len(app.background_tasks) == 0:
        return "No applications were hosting now."
    
    return "Your applications are now hosting normally."


@app.get('/restart')
async def self_restart():
    await bot.close()
    await bot.close_db()
    await instruction_queue.put("restart")    # Put "restart" to the queue to restart the web server
    return "Please Wait. Your server is now restarting..."


@app.after_serving
async def self_shutdown():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Actions after shutting down the Quart app (Ctrl + C or by command)
    """
    await bot.close()
    await bot.close_db()
    await instruction_queue.put("shutdown")   # Put "shutdown" to the queue to terminate the web server


async def run_server():
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Runs the Quart application using Hypercorn.
    """
    config = Config()
    config.bind = ["0.0.0.0:3000"]  # Custom PORT: 3000 for Azure and Docker
    config.debug = False

    try:
        # Run Hypercorn for the Quart app
        await serve(app, config)

    except asyncio.CancelledError:
        print("Server task cancelled. Shutting down Hypercorn...")

    except Exception as e:
        print(f"Error in server: {e}")

    finally:
        print("Hypercorn server has stopped.")


async def startup(queue):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Starts the Quart server.

    Parameters
    ----------
    queue : `asyncio.Queue`
        The instruction queue

    """
    global instruction_queue
    instruction_queue = queue
    server_task = asyncio.create_task(run_server())
    print("Hypercorn server started.")
    return server_task


async def cancel_server_task(server_task):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Cancel the server task

    Parameters
    ----------
    server_task: `Task[None]`
        The task from `startup()`

    """
    server_task.cancel()    # Cancel the server task

    try:
        await server_task    # Wait for the server task to finish

    except asyncio.CancelledError:
        print("Server task cancelled successfully.")


async def monitor_queue(queue, server_task):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Monitors the queue for instructions such as 'shutdown' or 'restart' in coroutine.

    Parameters
    ----------
    queue : `asyncio.Queue`
        The queue to monitor

    server_task: `Task[None]`
        The task from `startup()`

    """
    while True:
        instruction = await queue.get()
        match instruction:
            case "shutdown":
                await cancel_server_task(server_task)
                return   # Exit the main process gracefully

            case "restart" | "reboot":
                await cancel_server_task(server_task)
                print("Restarting application...")
                await asyncio.sleep(7)    # Time delay before restarting
                args = [sys.executable] + [sys.argv[0]]
                subprocess.call(args)    # Restart the script
                os._exit(0)  # Ensure exit the current subprocess after restart

            case _:
                raise ValueError(f"Unknown instruction for asyncio.Queue: {instruction}, must be either 'shutdown', 'reboot', or 'restart'.")
            
        await sleep(0.001)  # Minimal time delay to avoid busy-checking


async def main():
    """
    Main program execution logic.

    Rewrited with asynchronous approach.
    """
    queue = Queue()

    # Start the Quart server as an asyncio task
    server_task = await startup(queue)

    try:
        await monitor_queue(queue, server_task)    # Start monitoring the queue

    except asyncio.CancelledError:
        print("Main task cancelled. Cleaning up...")

    finally:
        print("Terminating server task...")
        server_task.cancel()

        try:
            await server_task

        except asyncio.CancelledError:
            print("Server task terminated.")

    print("Application halted.")


if __name__ == "__main__":
    asyncio.run(main())


