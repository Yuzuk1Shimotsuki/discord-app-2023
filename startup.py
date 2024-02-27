import discord
import asyncio
import os
from discord.ext import commands
from discord.ext.commands import ExtensionAlreadyLoaded, ExtensionNotLoaded, NoEntryPointError, ExtensionFailed
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# Custom errors
class NotBotOwnerError:
    def __repr__(self) -> str:
        return "Sorry, only the bot owner can perform this command."

class ExtensionNotFoundError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def return_msg(self) -> str:
        return f"I can't found the cog `{self.cog}` :pensive_face: ... Perhaps it was not a vaild input :thinking: ？"

class ReturnNoEntryPointError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def return_msg(self) -> str:
        return f"I can't found the `async def setup()` function in cog `{self.cog}` :pensive_face: ... Perhaps check the cog and try again :thinking: ？"
    
class ExtensionFailedError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def return_msg(self) -> str:
        return f"Some unexpected stuff happened while executing `{self.cog}`."

# Default configuration
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents, 
            command_prefix="?",
            self_bot=False, strip_after_prefix = True
        )

bot = Bot()


# Startup info
@bot.event
async def on_ready():
    print("-" * 140)
    print("Welcome to use the bot.")
    print(f"Bot Username: {bot.user.name} #{bot.user.discriminator}")
    print(f"Bot ID: {bot.application_id}")
    print("-" * 140)
    print("The bot is now ready for use!")
    print("-" * 140)

# Sync all cogs for latest changes
@bot.command() 
async def sync(ctx):
    if await bot.is_owner(ctx.author):
        synced = await bot.tree.sync()
        msg = await ctx.reply(f"Synced {len(synced)} command(s).")
        await asyncio.sleep(5)
        await msg.delete()
        await ctx.message.delete()
    else:
        await ctx.reply(NotBotOwnerError)

# Load cogs manually
@bot.command()
async def load(ctx, cog_name):
    if await bot.is_owner(ctx.author):
        # Front check if the cog was in the valid cog list or not
        if f"{cog_name}.py" not in os.listdir("./cogs"):
            return await ctx.reply(ExtensionNotFoundError(cog=cog_name).return_msg())
        try:
            await bot.load_extension(f"cogs.{cog_name}")
            await bot.tree.sync()
            msg = await ctx.reply(f"Cog `{cog_name}` has been loaded.")
            await asyncio.sleep(1)
            await msg.delete()
            await ctx.message.delete()
        except ExtensionAlreadyLoaded:
            return await ctx.reply(f"Cog `{cog_name}` is already loaded.")
        except NoEntryPointError:
            return await ctx.reply(ReturnNoEntryPointError(cog=cog_name).return_msg())
        except ExtensionFailed:
            return await ctx.reply(ExtensionFailedError(cog=cog_name).return_msg())
    else:
        await ctx.reply(NotBotOwnerError())

# Unload cogs manually
@bot.command()
async def unload(ctx, cog_name):
    if await bot.is_owner(ctx.author):
        if f"{cog_name}.py" not in os.listdir("./cogs"):
            # Front check if the cog was in the valid cog list or not
            return await ctx.reply(ExtensionNotFoundError(cog=cog_name).return_msg())
        try:
            await bot.unload_extension(f"cogs.{cog_name}")
            await bot.tree.sync()
            msg = await ctx.reply(f"Cog `{cog_name}` has been unloaded.")
            await asyncio.sleep(2)
            await msg.delete()
            await ctx.message.delete()
        except ExtensionNotLoaded:
            return await ctx.reply(f"Cog `{cog_name}` is already unloaded.")
        except NoEntryPointError:
            return await ctx.reply(ReturnNoEntryPointError(cog=cog_name).return_msg())
        except ExtensionFailed:
            return await ctx.reply(ExtensionFailedError(cog=cog_name).return_msg())
    else:
        await ctx.reply(NotBotOwnerError())

# Reload cogs manually
@bot.command()
async def reload(ctx, cog_name):
    if await bot.is_owner(ctx.author):
        # Front check if the cog was in the valid cog list or not
        if f"{cog_name}.py" not in os.listdir("./cogs"):
            return await ctx.reply(ExtensionNotFoundError(cog=cog_name).return_msg())
        try:
            await bot.reload_extension(f"cogs.{cog_name}")
            await bot.tree.sync()
            msg = await ctx.reply(f"Cog `{cog_name}` has been reloaded.")
            await asyncio.sleep(2)
            await msg.delete()
            await ctx.message.delete()
        except ExtensionNotLoaded:
            return await ctx.reply(f"Cog `{cog_name}` has not been loaded.")
        except NoEntryPointError:
            return await ctx.reply(ReturnNoEntryPointError(cog=cog_name).return_msg())
        except ExtensionFailed:
            return await ctx.reply(ExtensionFailedError(cog=cog_name).return_msg())
    else:
        await ctx.reply(NotBotOwnerError())

# Load extensions
async def load_extensions():
    print("\nLoading extensions...\n")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'cogs.{filename[:-3]}')

# Runs the bot
if __name__ == "__main__":
    load_dotenv()
    asyncio.run(load_extensions())

    for commands in bot.tree.walk_commands():
        print(commands.name)

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
