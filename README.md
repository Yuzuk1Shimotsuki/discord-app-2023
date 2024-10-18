# Discord Bot template in Python

A simple Discord application template in Python (using [discord.py](https://github.com/Rapptz/discord.py))

The application contains some core functions already but can be extended as needed. This guide assumes you have Python installed and a basic understanding of Python programming.

---

## What this bot can do right now?

This bot has been already equipped with the following functions:
- ChatGPT with gpt4o
- Music player
- Getting a discord user information or avatar
- Banning users
- Muting users
- Timeout users
- Writing an embed for you (Only works in server installation)

and so much more...

---

## Prerequisites

- **[Python](https://www.python.org/downloads/) 3.10 or later**
-  **[discord.py](https://github.com/Rapptz/discord.py) v2.4.0 or later**
-  **[Docker](https://www.docker.com/)** for hosting the bot.
-  **[Wavelink](https://github.com/PythonistaGuild/Wavelink) v3.4.1 or later** for the bot to play music in voice channels.

---

## Installation

You can simply run the following command in your terminal:
```bash
pip install -r requirements.txt
```
which will automatically install all required dependencies to your environment (except **docker** and **python3**)

---

## Before you use the bot

1. **Create a Discord Bot**:  
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Create a new **application**.
   - Inside your application, go to the **"Bot"** tab and click **"Add Bot"**.
   - Copy the **bot token** (you will need this later).

After that, you can install the bot as an **user-installed application**, or **inviting it to your server**: 
   - In the same Developer Portal, go to the **"OAuth2"** tab, generate an **OAuth2 URL** with the **`bot`** scope, and give your bot necessary permissions (such as `Send Messages` and `Read Messages`).
   - Visit the generated URL and follow the instructions from the website.

2. **Create a .env file and store your bot token**:
   - Create .env file in your root directory and copy the below template:
     
     ```bash
     DISCORD_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
     ```
     and replace `YOUR_BOT_TOKEN_HERE` with your bot token.

3. Great! You're now all set up!

---

## How to start up and host your bot 

To start the bot, open a terminal in the `discord-bot` directory and run:

```bash
python bot.py
```

If everything is set up correctly, you should see something like:

```
Logged in as `YourBotName`
```

which can be customized later on

Now, your bot is alive and should respond to commands in your Discord server. :D

Once you have checked that the bot can be hosted normally on your local machine, you can now try to host the bot 24/7 online.

There are plenty of ways to achieve this and I'm not gonna tell you all of them in there. This project is designed to host with docker and you can find more relevant information about it by googling.

---

## Future implemtations

This bot is a work in progress, and you can extend it with more functionality such as:

1. **Error Handling**: Add error handling for commands that don't exist or when users don't have permissions.
2. **Moderation Commands**: Add commands like `!kick`, `!ban`, or `!mute` for server moderation.
3. **Fun Commands**: Add more fun commands like `!roll` to roll a dice, or `!joke` to tell a random joke.
4. **Role Management**: Allow the bot to assign or remove roles from users.
5. **Database Integration**: Store user data or server configurations using a simple file system, SQLite, or an external database.

---
