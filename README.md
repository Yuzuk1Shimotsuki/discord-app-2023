<!-- PROJECT SHIELDS -->
<!--
*** Markdown "reference style" are in-used to all links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->



# Discord Bot template in Python

A simple Discord application template in Python (using [discord.py][discord.py_GitHub])

The application contains some core functions already but can be extended as needed. This guide assumes you have Python installed and a basic understanding of Python programming.

---

## What this bot can do right now?

The bot has already been equipped with these functions:
- ChatGPT AI chatbot
- Music player
- Getting a discord user information or avatar
- Banning users
- Muting users
- Timeout users
- Writing an embed for you (Only works in server installation)

and so much more...

---

## How can I use the bot?

If you want to self-host your own instance:

**Prerequisites**

   - **[Python][Python] 3.10 or later**
   -  **[discord.py][discord.py_GitHub] v2.4.0 or later**
   -  **[Docker][Docker]** for hosting the bot.
   -  **[MongoDB][MongoDB]** for storing custom configuration.
   -  **[Wavelink][Wavelink_GitHub] v3.4.1 or later** for the bot to play music in voice channels.

<br>

1. **Initialization**

   You can simply run the following command in your terminal (given that **[Docker][Docker]** and **[Python][Python]** have already been installed):
   ```bash
   pip install -r requirements.txt
   ```
   which will automatically install all required dependencies to your environment

2. **Create a Discord Bot**:
   1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   2. Create a new **application**.
   3. Inside your application, go to the **"Bot"** tab and click **"Add Bot"**.
   4. Copy the **bot token** (you will need this later).

   After that, you can install the bot as an **user-installed application**, or **inviting it to your server**:
     - In the same Developer Portal, go to the **"OAuth2"** tab, generate an **OAuth2 URL** with the **`bot`** scope, and give your bot necessary permissions (such as `Send Messages` and `Read Messages`).
     - Visit the generated URL and follow the instructions from the website.

3. **Configure MongoDB Atlas for data stroage**:

   1. **Create a MongoDB Atlas Account**
      1. Go to the [MongoDB Atlas website](https://www.mongodb.com/docs/atlas/getting-started/) and sign up for an account if you haven't.
      2. Follow the prompts to create a new account.
   
   2. **Create a Cluster**
      1. Once you're logged in, click on **"Create Cluster"**.
      2. Choose a name for your cluster and select a region closest to you.
      3. Select the **"Free Tier"** to start with a small-scale development environment.
      4. Click **"Create Cluster"**.
   
   3. **Configure Cluster Security**
      1. Go to the **"Security"** tab and click on **"IP Access List"**.
      2. Add your IP address to the list to ensure only your IP can access the cluster.
      3. Alternatively, you can set up user authentication for login.
   
   4. **Connect to Your Cluster**
      1. Go to the **"Connect"** tab and select **"Connect your application"**.
      2. Choose the appropriate driver and connection string for your application.
      3. Copy the connection string (URI) for later use and proceed to the next step.

4. **Create a .env file and store your bot token**:
   - Rename the `example.env` file as `.env`. Then, replace the empty string of `DISCORD_BOT_TOKEN` and `MONGO_DATABASE_URI` with your bot token and URI from MongoDB Atlas respectively.

5. Great! Now move on to <a href="#how-to-start-up-and-host-your-bot">How to start up and host your bot</a> for more instructions.

<br>

<details>
   <summary>
      Or, if you just want to try our features...
   </summary>
   &emsp;Head over to <a href="https://discord.com/oauth2/authorize?client_id=1158632119552196628">here</a> and <b>invite the bot to your server</b>, or install it as a <b>user-installed application</b> as you prefer.
</details>
<br>

---


## How to start up and host your bot

To start the bot, open a terminal in the `discord-bot` directory and run:

```bash
python startup.py
```

If everything is set up correctly, you should see something like:

```
----------------------------------
Welcome to use the bot.
Bot Username: `BOT_NAME` #`BOT_DISCRIMINATOR`
Bot ID: {bot.application_id}
----------------------------------
The bot is now initiated and ready for use!
----------------------------------
```

which can be customized later on

Now, your bot is alive and should respond to commands in your Discord server. :D

Once you have checked that the bot can be hosted normally on your local machine, you can now try to host the bot 24/7 online.

There are plenty of ways to achieve this and I'm not gonna tell you all of them in there. This project is designed to host with docker and you can find more relevant information about it by googling.

- Docker Compose

> [!NOTE]
> Make sure that Docker is already installed on your computer or server.


1. Clone this Repository
```
git clone [somthing]
```

2. Navigate to project directory by `cd`
```
cd [somthing]
```

3. Pass your `.env` file to the project directory
> [!WARNING]
> NEVER push your `.env` file directly to this repo as this will cause data compromisation and triggers Discord security action, and worst case could get your account terminated!

4. Launch the bot with your `.env` file created earlier
```
docker compose up
```

5. If nothing goes wrong, congratulations :tada:! You're now all set up!

> [!NOTE]
> Support of using docker run has been removed since version 2.0

---

## Future implemtations

The bot is still working in progress. More functionality will be added in the future such as:

- **Role Management**: Allow the bot to assign or remove roles from users.
- **Third-party database integration**: Store user data or server configurations using a simple file system, SQLite, or an external database besides [MongoDB][MongoDB].

---



<!--Links in use in this markdown for refrences-->

[discord.py_GitHub]: https://github.com/Rapptz/discord.py

[Discord-DeveloperPortal]: https://discord.com/developers/applications

[MongoDB]: https://www.mongodb.com/

[Python]: https://www.python.org/downloads/

[Docker]: https://www.docker.com/

[MongoDB]: https://www.mongodb.com/

[Wavelink_GitHub]: https://github.com/PythonistaGuild/Wavelink
