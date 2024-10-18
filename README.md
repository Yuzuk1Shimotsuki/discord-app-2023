# Simple Discord Bot template in Python (using [discord.py](https://github.com/Rapptz/discord.py))

This document outlines a simple Discord bot project that is currently a work in progress, built using the `discord.py` library. The bot contains some core functions already but can be extended as needed. This guide assumes you have Python installed and a basic understanding of Python programming.

## Prerequisites

Before starting, ensure you have the following:

1. **Python 3.10 or later**: Make sure Python is installed. You can download it from [here](https://www.python.org/downloads/).
2. **Discord.py library**: Install the `discord.py` library, which is essential for creating the bot.

You can install the `discord.py` library using pip:

```bash
pip install -U discord.py
```

3. **Create a Discord Bot**:  
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Create a new application.
   - Inside your application, go to the "Bot" tab and click "Add Bot".
   - Copy the bot token (you will need this later).

4. **Invite the Bot to Your Server**:  
   - In the same Developer Portal, go to the "OAuth2" tab, generate an OAuth2 URL with the `bot` scope, and give your bot necessary permissions (such as `Send Messages` and `Read Messages`).
   - Use this URL to invite the bot to your server.

---

## Project Structure

We will create a simple bot that responds to basic commands like `!hello` and `!ping`. The project structure will be as follows:

```
discord-bot/
│
├── bot.py
└── requirements.txt
```

---

## Step-by-Step Guide

### 1. Setting Up the Bot Code

Create a file called `bot.py` in the root directory. This file will contain the bot's logic.

```python
import discord
from discord.ext import commands

# Set up the bot with a prefix for commands
intents = discord.Intents.default()
intents.message_content = True  # Ensure this is enabled for message content access
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Command: Respond to "ping"
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# Command: Respond to "hello"
@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author.name}!')

# Run the bot using your token
if __name__ == '__main__':
    TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Replace with your bot's token
    bot.run(TOKEN)
```

### 2. Explanation of the Code

- **Imports**:
  - `discord`: The core library to interact with Discord's API.
  - `commands`: A module from `discord.ext` that allows us to define bot commands easily.

- **Bot Setup**:
  - The bot is initialized with a command prefix `!`. This means users will trigger commands by typing `!command` in the chat.
  - The `intents` object is used to specify what events the bot can listen to. Here, we enable `message_content` to allow the bot to read messages.

- **Bot Events**:
  - The `on_ready()` function is triggered when the bot successfully connects to Discord. It prints a message to the console indicating the bot is online.

- **Bot Commands**:
  - `!ping`: This command sends back "Pong!" when a user types `!ping`.
  - `!hello`: This command greets the user by their Discord username.

### 3. Running the Bot

To start the bot, open a terminal in the `discord-bot` directory and run:

```bash
python bot.py
```

If everything is set up correctly, you should see something like:

```
Logged in as YourBotName
```

which can be customized later on

Now, your bot is live and should respond to commands in your Discord server. :D

---

## Future Extensions

This bot is a work in progress, and you can extend it with more functionality such as:

1. **Error Handling**: Add error handling for commands that don't exist or when users don't have permissions.
2. **Moderation Commands**: Add commands like `!kick`, `!ban`, or `!mute` for server moderation.
3. **Fun Commands**: Add more fun commands like `!roll` to roll a dice, or `!joke` to tell a random joke.
4. **Role Management**: Allow the bot to assign or remove roles from users.
5. **Database Integration**: Store user data or server configurations using a simple file system, SQLite, or an external database.

---

## Example of Adding a New Command: `!roll`

Here’s a quick example of how you can add a dice rolling feature to the bot.

```python
import random

# Command: Roll a dice
@bot.command()
async def roll(ctx, number: int):
    if number < 1:
        await ctx.send("Please specify a number greater than 0.")
    else:
        result = random.randint(1, number)
        await ctx.send(f'You rolled a {result}!')
```

Now, users can type `!roll 6` to roll a 6-sided dice.

---

## Requirements File (Optional)

To make it easier for others (or yourself) to install the necessary dependencies, a `requirements.txt` file is already included in this project.

```txt
discord.py>=2.4.0
```

To install dependencies from this file, run:

```bash
pip install -r requirements.txt
```

---

## Conclusion

This simple Discord bot is just the beginning. With `discord.py`, you have access to a wide variety of features and events. As you continue developing your bot, you can add more commands, integrate APIs, and handle more complex server actions.

Feel free to modify and expand this bot as needed for your project!
