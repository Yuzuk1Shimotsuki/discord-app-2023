import discord
import asyncio
import os
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


# Custom errors
class NotBotOwnerError:
    def __repr__(self) -> str:
        return "Sorry, only the bot owner can perform this command."

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
        msg = await ctx.reply(NotBotOwnerError)

# Load cogs manually
@bot.command()
async def load(ctx, cog):
    if await bot.is_owner(ctx.author):
        if bot.get_cog(cog):
            await bot.add_cog(cog)
            await bot.tree.sync()
            msg = await ctx.reply(f"Cog `{cog}` has been loaded.")
            await asyncio.sleep(1)
            await msg.delete()
            await ctx.message.delete()
        else:
            await ctx.reply(f"I can't load the cog `{cog}` :pensive_face: ... Perhaps it was not a vaild input :thinking: ？")
    else:
        msg = await ctx.reply(NotBotOwnerError())

# Unload cogs manually
@bot.command()
async def unload(ctx, cog):
    if await bot.is_owner(ctx.author):
        if bot.get_cog(cog):
            await bot.remove_cog(cog)
            await bot.tree.sync()
            msg = await ctx.reply(f"Cog `{cog}` has been unloaded.")
            await asyncio.sleep(1)
            await msg.delete()
            await ctx.message.delete()
        else:
            await ctx.reply(f"I can't unload the cog `{cog}` :pensive_face: ... Perhaps it was not a vaild input :thinking: ？")
    else:
        msg = await ctx.reply(NotBotOwnerError())

# Reload cogs manually
@bot.command()
async def reload(ctx, extension):
    if await bot.is_owner(ctx.author):
        if bot.get_cog(extension):
            bot.reload_extension(extension)
            await bot.tree.sync()
            msg = await ctx.reply(f"`{extension}` has been reloaded.")
            await asyncio.sleep(1)
            await msg.delete()
            await ctx.message.delete()
        else:
            await ctx.reply(f"I can't reload the cog `{extension}` :pensive_face: ... Perhaps it was not a vaild input :thinking: ？")
    else:
        msg = await ctx.reply(NotBotOwnerError())

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
