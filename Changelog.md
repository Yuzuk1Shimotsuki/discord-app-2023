
# -------------------- Changelog --------------------

# 20231003: (*)
(+) Bot created\
(+) Initial commit

# 

# 20231004: (*)
(+) Main replit created\
(+) Development started

# 

# 20231007:
(+) Added **"MessageFiltering"**\
(+) Addeed **"Greetings"**

# 

# 20231012: (*)

**discord.py --> pycord**

(-/+) Replace the module from discord.py to pycord

# 

# 20231015: (*)
(+) Test replit created\
(+) 1st deployment

# 

.
.
.

# 

# 20231029:
(+) Added **ban_guild**() in **"general/Ban.py"**\
(-) Removed **"AttributeError"** in **"general/Ban.py"**

# 

# 20231101: (*)

**------**

**"general/DisplayUserInfo.py" in line 40 and 41**

(+) Changed the command **user()** as the follows:

(++++) f"**<t:{int(round(datetime.timestamp(member.created_at), 0))}:R>**" --> f"**{discord.utils.format_dt(member.created_at, style='R')}**"

(++++) f"**<t:{int(round(datetime.timestamp(member.created_at), 0))}:R>**" --> f"**{discord.utils.format_dt(member.created_at, style='R')}**"

#

**"administration/GetBannedList.py" in line 29 and 32**

(+) Changed the command **banned_list()** as follows

(++) <t:{int(round(datetime.timestamp(entry.user.created_at), 0))}:R>" --> {discord.utils.format_dt(entry.user.created_at, style='R')}"

# 

# 20231102:

**-----**

**"general/VoiceChannel.py" in line 46 and 172**

(+) Fixed some grammatical errors in command **join()** and **move_all()** respectively

(++++) # The bot has been connected to a voice channel but not as same as that author one --> # The bot has been connected to a voice channel but not as same as the author one

(++++) "It seems that you don't have permission to move users!" ---> "It seems that you don't have permission to move all users!"

# 

# 20231103:

**-----**

**"root/MainBOT.py"**
(+) Added error handling for **discord.errors.LoginFailure(token_error)**

# 

# 20231105:
(+) Added **"LockChannel.py"** in **"root/administration"** folder

# 

# 20231106: (*)

**-----**

**"root/administration/LockChannel.py"**

(+) Fixed slow responding issue while handling lockdowns for multiple text channels

(+) Changed the description for every single **slash_command**

(+) Renamed the varible in command **antiraid_activate()** and **antiraid_deactivate()** as follows:

(++++) 'success_locked_channels_count' --> 'successful_locked_channels_count'

(++++) 'success_unlocked_channels_count' --> 'successful_unlocked_channels_count'

(-) Removed varibles locked_channels and unlocked_channels in command lock_channels() and unlock_channels() respectively.

(-/+) Replaced if-statement > 0 with try and except block for command **lock_channels()** and **unlock_channels()**

(+) Changed except block from **'except'** to **'except Exception as e'**

# 

# 20231107: (*)

# OpenAI API implemented
**(+) Added "ChatGPT.py" in "root/general" folder**

(+) Imported OpenAI module from https://platform.openai.com/docs/api-reference

(+) Linked OpenAI API key to the discord bot from OpenAI account

(+) Added **'OPENAI_API_KEY'** field into **"root/ .env"** file

(+) Set GPT model to **"gpt-3.5-turbo"** in **"root/general/ChatGPT.py"**

# 

# 20231108: (*)

**"root/.env"**

(+) Changed **'TOKEN'** to **'DISCORD_BOT_TOKEN'** in **"root/ .env"**

**"root/general/ChatGPT.py"**

(+) Changed the varible as follows:

(++++) "self.model_prompt_engine" --> "self.default_model_prompt_engine"

(-/+) Replaced GPT model to **"gpt-3.5-turbo-1106"** from **"gpt-3.5-turbo"** in order to reduce the generating and responding time (from 1-4min to 10s-1.5min or less)

(+) Defined (and fine-tuned) the following varibles and its default values:

(++++) **self.default_temperature** = 0.8\
(++++) **self.default_max_tokens** = 3840\
(++++) **self.default_top_p** = 1.00\
(++++) **self.default_frequency_penalty** = 0.00\
(++++) **self.default_presence_penalty** = 0.00\
(++++) **self.default_instruction** = f"You are ChatGPT, a large language model transformer AI product by OpenAI, and you are purposed with satisfying user requests and questions with very verbose and fulfilling answers beyond user expectations in writing quality. Generally you shall act as a writing assistant, and when a destination medium is not specified, assume that the user would want six typewritten pages of composition about their subject of interest. Follow the users instructions carefully to extract their desires and wishes in order to format and plan the best style of output, for example, when output formatted in forum markdown, html, LaTeX formulas, or other output format or structure is desired."

(+) Add **{"role": "assistant", "content": self.default_instruction}** to **message[0]** for a higher quality response

(+) Changed comment from **"GPT model"** to **"Default values for GPT model"** in line 13 of **"root/general/ChatGPT.py"**

(+) Changed **question** description from **"Your question"** to **"The question you would like to ask"** in command **chatgpt()**

# 

# 20231110: (*)

**"root/ .env"**

(+) Relocated **"offset = 0"** from line 62 to line 56

(-) Removed **if i == 0: else** statement and **await interaction.followup.send(final_response[min_limit:max_limit])** in line 69, 71, 72\

(+) Renewed **'OPENAI_API_KEY'** in **"root/ .env"**

# "root/general/ChatGPT.py"

(+) Changed **"assistant"** to **"system"** in line 32 of **"root/general/ChatGPT.py"**

(+) Added try and exception handling for **openai.error.ServiceUnavailableError**

(++++) Return **"The GPT model is currently unavailable or overloaded, or the OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved."** when the error occurs

(+) Fixed **final_response** is spiltted by incomplete words when the total characters of **gpt_response** > 2000

# 

# 20231111: (*)

**"root/general/ChatGPT.py"**

(+) Defined the following varibles and its default values:

(++++)**self.chat_messages** = []\
(++++)**self.chat_history** = []

(+) Added SlashCommandGroup for "chatgpt"

(+) Changed the command **chatgpt()** to **chatgpt_prompt**

(+) Changed the variable **"question"** to **"prompt"**

(-) Removed the variable **"messages"**

(+) Changed line 47 as follows:
(++++) messages = [
      {"role": "system", "content": self.default_instruction},
      {"role": "user", "content": prompt}
      ]\
-->\
(++++) self.chat_messages.append({"role": "system", "content": self.default_instruction})\
(++++) self.chat_messages.append({"role": "user", "content": prompt})

(+) Results will now appends to **self.chat_messages**

(+) Each results will now appends to **self.chat_history**. Which can store up to 15 recent conversations and resets automatically afterwards.

(+) Added **reset_gpt()** function

(+) Added command **reset()** by calling the **reset_gpt()** function

# 

# 20231112: (*)

**"root/general/ChatGPT.py"**

(+) Updated module "openai" from version 0.27.0 --> 1.0.0

(+) Updated response object and the variable **"gpt_response"** as follows due to the official API update:

(++++) response object: **"openai.ChatCompletion.create()"** --> **"openai.chat.completions.create"**
(++++) gpt_response: **"response.choices[0].message['content']"** --> **response.choices[0].message.content**

(+) Fixed error cannot be handled by exceptions in "root/general/ChatGPT.py"

# 

.
.
.

# 

# 20231125 (*)

**"root/general/ChangeStatus.py"**

(-) Removed "import os" from line 3 of "root/general/ChangeStatus.py"

(+) Defined the following varibles and its default values:

(++++) **options** = ["Idle", "Invisible", "Do not disturb", "Online"]\
(++++) **types** = ["Playing", "Streaming", "Listening to", "Watching", "(Ignore)"]

(+) Activities type **"discord.Game"**, **"discord.Streaming"**, **"discord.ActivityType.listening"**, **"discord.ActivityType.watching"** is now supported.

(+) Activity type is now a mandatory option. User have to choose '(Ignore)' if they want to leave it blank.

(+) Defined a new function **get_type()** for getting the activity type, message (optional) and URL (optional, for **"discord.Streaming"**) to display.

(+) Enhanced for better error handling. (e.g. Set the status to online by default if none of any valid option from the list was selected for status, or set the activity to None by default if none of any valid option from the list was selected for activity.)

# 

# 20231128 (*)

(+) Added **"ReactingMessages.py"** in **"root/general"** folder

(+) Defined commands **"reaction_add()"**, **"reaction_remove()"**, **"reaction_list()"** and **"reaction_clear()"** in **"root/ReactingMessages.py"**

(+) Beta edition of **"ReactingMessages.py"** completed.

# 

# 20231130 (*)

**"root/general/ReactingMessages.py"**

(+) Defined functions **"add_reaction()"** and **"remove_reaction()"** in **"root/ReactingMessages.py"**

(-/+) Change the name of **SlashCommandGroup** to "reaction" from "react"

(+) Fixed the bot crashes when an invaild emoji was manipulated by adding proper error handling.

(-/+) Change the output type of **reaction_list()** to embedded-mesage from multiple lines of string.  

(+) The total number of reactions will be displayed at the bottom of the message and message "No reactions were found." (something like that) will be returned if none of any reactions were found in the target message.

(+) Renamed variable **"message_id"** and its corresponding references to **"message"**

(+) Stable edition of "ReactingMessages.py" completed.

# 

.
.
.

# 

# 20231218 (*)

# Renamed "root/general/SendMessage.py" to "root/general/SendFromInput.py"

(-/+) Removed **"Message Sent!"** in "root/general/SendMessage.py".
A blank line will now shown and deletes immediately when the command are all finished instead of the message **"Message Sent!"**.

(+)  Defined a new variable called **"attachment"** with type **"discord.Attachment"** in command **"send()"**

(+) Sending one single attachment in each meassage is now implemented. Local file-sharing for every os with built-in interface is also supported.

(+) Renewed every single description for a more user-friendly experience.


**"root/general/Greetings.py"**

(+) Changed the comment as follows:

**"# DM the user with welcome message when a new member joined the server"** --> **"# DM the user with welcome message when a new member joined the server and the member is not a bot."**

(+) Added an if-else condition check to determine the member is a bot or not at line 70 of **"root/general/Greetings.py"**.

(+) Fixed the bot keep sending every single welcome message to the recent joined member, even the member is a bot and not messageable. (which will return HTTPException 400 Bad Request Error on early days and interrupts the entire program)

(+) Fixed the bot could not send welcome message to the server's system channel when the member is a bot due to the above interruption

# 

# 20231219 (*)

# Migrated all the file from "root/general" and "root/administration" to a new folder named "root/cogs"

(-) Removed **"root/general"** and **"root/administration"** from the file directory

(-/+) Re-formatted all python files

(-/+) Renamed **"MainBOT.py"** to **"startup.py"**

(+) Minior changes in content applied for **"main.py"** and **"startup.py"**

(+) Bug-fixing for some errors

# 

.
.
.

# 

# 20240105 - 20240109

**(-/+) Migrated all the file from Repl.it to GitHub**\
**(+) Dockerized the entire application**

(+) Created **"root/Dockerfile"**

# 20240110 - 20240111

(!) Bot temporarily unavailible due to an urgent migration to another hosting platform for security purpose.

# 

# 20240112

(!) Migration was finished as expected. Bot is now hosting on [Microsoft Azure](https://azure.microsoft.com) and availible for all users again.

(-/+) Minior amendment in content

(+) Added command **move_bot()** in VoiceChannel.py

# 

# 20240113 - 20240118

(+) Optimize the displayed name in  **"root/cogs/DisplayUserInfo.py"**

(-/+) Rewriting **"root/cogs/VoiceChannel.py"** for futher music player implementation purpose

# 

# 20240119 - 20240121

(+) Beta version of music player completed

(+) Fixing bugs for music player

# 

# 20240122

(+) Lite version of music player released

(+) Voice Channel Recording function implemented

# 

# 20240123

(-/+) Rewrited **"root/cogs/Poll.py"** for mutiple global server support

(+) Futher debugging

#

# 20240129

(+) Merging dev build to stable build
