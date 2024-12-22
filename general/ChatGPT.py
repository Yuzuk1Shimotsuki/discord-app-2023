import discord
import os
import tempfile
import openai
import ast
import re
from datetime import datetime
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from discord.ui import Modal, TextInput
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, List
from errorhandling.ErrorHandling import *

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")

openai_client = OpenAI(api_key=API_KEY)

# Ensure assistants exist in the database
async def initialize_assistants(db_cluster):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Create assistants and ensure assistants exist in the database

    Note: This operation requires a stable database and network connection

    Parameters
    ----------
    db_cluster: `motor.AsyncIOMotorClient`
        The cluster object from MongoDB.
    
    Returns
    ----------
    None
    
    """
    database = db_cluster["chatgpt"]
    assistants_collection = database["assistants"]
    assistants = {
        "premium": {
            "name": "Premium Assistant",
            "model": "gpt-4-1106-preview",
            "tools": [
                {"type": "file_search"},
                {"type": "code_interpreter"}
            ],
            "instructions": f'''
            You are ChatGPT, a large language model transformer AI product by OpenAI, and you are 
purposed with satisfying user requests and questions with very verbose and fulfilling answers beyond user expectations, as detailed as possible. For example, if the user asking 'is md5 a encryption method?', you should answer directly first then provide
some reasons to support your evidence, and provide some alternative encryption method if and only necessary, also if the user wish to test the system, you should response something such as greetings with no more than 20 words. Follow
the users instructions carefully to extract their desires and wishes in order to format and plan the best style of output, no need to summarize your content unless
other specified by user. For example, when output formatted in forum markdown, html, LaTeX formulas, or other output format or structure is desired.
            ''',
            "access_level": "premium"
        },
        "normal": {
            "name": "Basic Assistant",
            "model": "gpt-4-1106-preview",
            "tools": [{"type": "file_search"}],
            "instructions": "You are the Normal Assistant. Provide clear and concise answers to fulfill user queries.",
            "access_level": "basic"
        },
        "trial": {
            "name": "Trial Assistant",
            "model": "gpt-3.5-turbo",
            "tools": [],
            "instructions": "You are the Trial Assistant. Provide responses to fulfill user queries.",
            "access_level": "trial"
        }
    }

    for level, assistant_data in assistants.items():
        existing = await assistants_collection.find_one({"access_level": level})
        if not existing:
            assistant = openai_client.beta.assistants.create(
                name=assistant_data["name"],
                model=assistant_data["model"],
                tools=assistant_data["tools"],
                instructions=assistant_data["instructions"]
            )
            await assistants_collection.insert_one({
                "access_level": level,
                "assistant_id": assistant.id,
                "name": assistant_data["name"]
            })

async def get_access_level(db_cluster, interaction: Interaction, user_id: int, guild_id: int):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Check the access level of a server or user.

    Default to `'trial'` if not specified in the database.

    Note: This operation requires a stable database and network connection

    Parameters
    ----------
    db_cluster: `motor.AsyncIOMotorClient`
        The cluster object from MongoDB.

    user_id: int
        The user's ID.

    guild_id: int
        The guild's ID.
    
    Returns
    ----------
    str:
        The maximum access level of user / guild.
    
    """
    database = db_cluster["chatgpt"]
    user_access_collection = database["user_access"]
    server_access_collection = database["server_access"]
    try:    # Check if the user is the bot owner
        user = await interaction.client.fetch_user(user_id)    # Fetch the user
    except discord.NotFound as e:
        if e.status == 404 and e.code == 10013:    # User not found
            user = None
        else:
            raise e
    if user and await interaction.client.is_owner(user):
        return "premium"    # Owner (or team members) always get premium access. Obviously.

    # Get user access level from the database
    user_access_entry = user_access_collection.find_one({"_id": user_id})
    user_access_level = user_access_entry["access_level"] if user_access_entry else "trial"
    
    # Get guild access level from the database (if guild_id is provided)
    if guild_id:
        server_access_entry = server_access_collection.find_one({"_id": guild_id})
        server_access_level = server_access_entry["access_level"] if server_access_entry else "trial"
    else:
        server_access_level = "trial"    # Default when no guild ID is provided, or the interaction isn't from a server

    # Compare and return the highest access level
    print(max(server_access_level, user_access_level, key=lambda level: access_level_priority(level)))
    return max(server_access_level, user_access_level, key=lambda level: access_level_priority(level))


def access_level_priority(level: str):
    """
    Define a priority order for access levels.
    Higher levels are given higher priority.

    Parameters
    ----------
    level: str
        The level returned from `get_access_level()`, can be either "premium", "basic" or "trial".

    Returns
    ----------
    int:
        The access level represented in ingeter, Higher value means higher priority.

    """
    priority = {
        "trial": 0,
        "basic": 1,
        "premium": 2
        }
    return priority.get(level.lower(), -1)    # Default to -1 if the level is unknown.


async def get_assistant_by_access_level(db_cluster, access_level: int):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Retrieve the assistant ID for the given access level.

    Note: This operation requires a stable database and network connection

    Parameters
    ----------
    db_cluster: `motor.AsyncIOMotorClient`
        The cluster object from MongoDB.
        
    access_level: int
        The level returned from `access_level_priority()`.
    
    Returns
    ----------
    int:
        The corresponding assistant ID based on user's / server access level.

    Raises
    ----------
    ValueError:
        Assistant ID were not found in the database for user's / server access level.

    """
    database = db_cluster["chatgpt"]
    assistants_collection = database["assistants"]
    assistant = await assistants_collection.find_one({"access_level": access_level})
    if assistant:
        return assistant["assistant_id"]
    else:
        raise ValueError(f"No assistant found for access level: {access_level}")


async def get_or_create_channel_entry(db_cluster, channel_id, guild_id, assistant_id, is_thread=False):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Get or create a MongoDB entry for a channel or thread

    Parameters
    ----------
    db_cluster: `motor.AsyncIOMotorClient`
        The cluster object from MongoDB.
        
    channel_id: int
        The channel ID.

    guild_id: int
        The guild ID.
    
    is_thread: bool
        Checks if the channel is a thread or not.

    
    Returns
    ----------
    dict:
        The entry dictionary of a channel.

    """
    database = db_cluster["chatgpt"]
    channels_collection = database["discord_channels"]
    entry = await channels_collection.find_one({"channel_id": channel_id})
    if not entry:
        openai_thread = openai_client.beta.threads.create()
        entry = {
            "channel_id": channel_id,   # Channel ID or Thread ID
            "guild_id": guild_id,
            "is_thread": is_thread,
            "openai_thread_id": openai_thread.id,
            "assistant_id": assistant_id,
            "messages": [],
            "attachments": [],
        }
        await channels_collection.insert_one(entry)
    return entry


async def save_attachment_temporarily(attachment):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Save the attachment to a temporary file with a proper extension.
    
    Parameters
    ----------
    attachment: discord.Attachment
        The file attachment to be saved.

    extension: str
        The extension for the temporary file (e.g., '.txt', '.pdf').

    Returns
    ----------
    str:
        The path to the saved temporary file.

    Raises:
    ----------
    ValueError:
        The file extension was not supported.

    """
    extension = f".{attachment.filename.split('.')[-1]}" if '.' in attachment.filename else ''
    if extension not in ['.txt', '.pdf', '.csv', '.json', '.png', '.jpg', '.mp4']:  # Add other supported extensions
        raise ValueError(f"Unsupported file extension: {extension}")

    # Create a temporary file with the correct extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        await attachment.save(temp_file.name)
        return temp_file.name


async def upload_file_to_openai(local_path):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Upload a file to OpenAI.

    Parameters
    ----------
    local_path: str
        The file path from local device.
    
    Returns
    ----------
    `Files`:
        An uploaded OpenAI file object.

    """
    with open(local_path, "rb") as file:
        return openai_client.files.create(file=file, purpose="assistants")


def discord_message_formatter(content: str, limit: Optional[int] = 2000) -> List[str]:
    """
    Format and split a message into chunks that adhere Discord's 2000 characters and markdown limitation.

    Note that this is a rewrite and hopefully will support all languages. The function attempts to split
    at natural boundaries (newlines, spaces) first, before falling back to character-level splits if necessary.

    Parameters
    ----------
    content : str
        The message to be formatted and split. Can contain any language, including mixed content
        and markdown formatting.

    limit : `Optional[int]`
        Maximum number of characters per chunk (default is 2000, Discord's message limit)

    Returns
    -------
    `List[str]`
        A list of formatted strings from the message, each no longer than the specified limit.

    Examples
    --------
    >>> text = "This is a long message" * 1000
    >>> chunks = discord_message_formatter(text)
    >>> all(len(chunk) <= 2000 for chunk in chunks)
    True

    >>> # Works with Chinese, Japanese and other languages
    >>> text = "這是一個很長的訊息" * 1000
    >>> chunks = discord_message_formatter(text)
    >>> all(len(chunk) <= 2000 for chunk in chunks)
    True

    >>> text = "これは長いメッセージです。" * 1000
    >>> chunks = discord_message_formatter(text)
    >>> all(len(chunk) <= 2000 for chunk in chunks)
    True

    """

    content = content.replace("######", "###").replace("#####", "###").replace("####", "###")   # Adjust Markdown headers

    def has_unclosed_markdown(text):
        patterns = [r'\*', r'\_', r'\`', r'\~\~', r'\|\|']
        return any(len(re.findall(p, text)) % 2 != 0 for p in patterns)

    def find_last_markdown(text):
        markdown = re.findall(r'(\*+|\_+|\`+|\~\~|\|\|)', text)
        return markdown[-1] if markdown else ''

    def split_cjk(text):
        return [x for x in re.findall(r'[\u4e00-\u9fff]|[^\u4e00-\u9fff]+', text) if x.strip()]    # Split text while preserving both words and CJK characters

    chunks = []
    current_chunk = ''

    segments = split_cjk(content)    # Use CJK-aware splitting

    for segment in segments:
        test_chunk = current_chunk + ('' if not current_chunk else ' ' if segment.isspace() or not any('\u4e00' <= c <= '\u9fff' for c in segment) else '') + segment
        
        if len(test_chunk) <= limit:
            current_chunk = test_chunk
        else:
            if has_unclosed_markdown(current_chunk):
                markdown = find_last_markdown(current_chunk)
                if len(current_chunk + markdown) <= limit:
                    current_chunk += markdown

            chunks.append(current_chunk)
            current_chunk = segment

    if current_chunk:
        chunks.append(current_chunk)

    # Final verification and splitting of any oversized chunks
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > limit:
            # If still too long, split by character while preserving markdown
            temp_chunk = ''
            for char in chunk:
                if len(temp_chunk + char) > limit:
                    final_chunks.append(temp_chunk)
                    temp_chunk = char
                else:
                    temp_chunk += char
            if temp_chunk:
                final_chunks.append(temp_chunk)
        else:
            final_chunks.append(chunk)

    return final_chunks


async def openai_error_embed_handler(interaction, e, title):
    """
    This function is a [coroutine](https://docs.python.org/3/library/asyncio-task.html#coroutine).

    Handling common errors from OpenAI API.

    Parameters
    ----------
    interaction: `Interaction`
        The interaction from Discord.

    e: `sys.stderr`
        Error parameter from OpenAI API
    
    title: str
        The title of the embed
    
    Returns
    ----------
    None

    """
    error_embed = discord.Embed(
        title=title,
        timestamp=datetime.now(),
        color=discord.Colour.red()
    )
    # Extract error details
    error_message = getattr(e, 'message', 'An unknown error occurred.')

    if hasattr(e, "message"):
        # Find the first '{' in the string, which indicates the start of the dictionary
        dict_start = error_message.find("{")
        if dict_start == -1:
            raise ValueError("No dictionary found in the string.")
        
        # Extract the substring starting from the first '{'
        dict_string = error_message[dict_start:]
        
        # Safely evaluate the string into a Python dictionary
        error_dict = ast.literal_eval(dict_string)
        error_message = error_dict["error"]["message"] if hasattr(e, "status_code") else error_dict["message"]

    error_status_code = getattr(e, 'status_code', 'N/A')
    error_type = getattr(e, 'type', 'N/A')
    error_param = getattr(e, 'param', 'N/A')
    error_code = getattr(e, 'code', 'N/A')

    # Add fields to the embed
    error_embed.add_field(
        name='\u200b',
        value=error_message,
        inline=False
    )
    error_embed.add_field(
        name='\u200b',
        value=f"", 
        inline=False
    )
    error_embed.add_field(
        name="Error details:",
        value=f"Status code: {error_status_code}\nType: {error_type}\nParam: {error_param}\nCode: {error_code}",
        inline=False
    )

    await interaction.followup.send(embed=error_embed)


# ----------<ChatGPT>----------


class ChatGPTModal(Modal):
    """
    A Discord Modal to collect user input for the ChatGPT command.
    """

    content = TextInput(
        label="Content",
        style=discord.TextStyle.paragraph,
        placeholder="Your content here...",
        required=True,
        max_length=4000
    )


    def __init__(self, db_cluster):
        self.db_cluster = db_cluster    # Connect to MongoDB
        super().__init__(title="Talk to our AI assistant")


    async def on_submit(self, interaction: Interaction):
        """
        Handle modal submission.
        """
        database = self.db_cluster["chatgpt"]
        channels_collection = database["discord_channels"]
        await interaction.response.defer()
        wait_message = await interaction.followup.send("<a:LoadingCustom:1295993639641812992> *Waiting for GPT to respond...*", wait=True)

        try:
            channel_id = interaction.channel.id
            user_id = interaction.user.id
            guild_id = interaction.guild.id if interaction.guild else None
            is_thread = isinstance(interaction.channel, discord.Thread)

            # Determine access level
            access_level = await get_access_level(self.db_cluster, interaction, user_id, guild_id)

            try:
                assistant_id = await get_assistant_by_access_level(self.db_cluster, access_level)

            except ValueError as e:
                return await interaction.followup.send(str(e), ephemeral=True)

            entry = await get_or_create_channel_entry(self.db_cluster, channel_id, guild_id, assistant_id, is_thread)
            content = self.content.value

            # Send message to OpenAI
            openai_thread_id = entry.get("openai_thread_id")
            if not openai_thread_id:
                openai_thread = openai_client.beta.threads.create()
                openai_thread_id = openai_thread.id
                await channels_collection.update_one(
                    {"channel_id": channel_id}, {"$set": {"openai_thread_id": openai_thread_id}}
                )

            # Send the message to OpenAI
            openai_client.beta.threads.messages.create(
                thread_id=openai_thread_id,
                role="user",
                content=content,
                attachments= [{"file_id": attachment["file_id"], "tools": [{"type": "file_search"}]} for attachment in entry.get("attachments", [])] or None
            )


            user_message = {"role": "user", "content": content}
            await channels_collection.update_one(
                {"channel_id": channel_id}, {"$push": {"messages": user_message}}
            )

            # Fetch OpenAI's reply
            openai_client.beta.threads.runs.create_and_poll(
                thread_id=openai_thread_id, assistant_id=assistant_id
            )

            all_messages = openai_client.beta.threads.messages.list(
                thread_id=openai_thread_id
            )

            # Combine all parts of the assistant's reply
            assistant_reply = "".join(
                message.text.value for message in all_messages.data[0].content
            )

            reply_message = {"role": "assistant", "content": assistant_reply}
            await channels_collection.update_one(
                {"channel_id": channel_id}, {"$push": {"messages": reply_message}}
            )

            # Format and send response
            quote = f"> {interaction.user.mention}: **{content}**{discord.utils.escape_markdown(' ')}"
            edited_response = f"{quote}\n{discord.utils.escape_markdown(' ')}\n{assistant_reply}"
            
            formatted_responses = discord_message_formatter(edited_response)

            for msg in formatted_responses:
                await interaction.followup.send(msg)

            await wait_message.delete()
        
        # Handling expections from OpenAI API errors
        except openai.APITimeoutError as e:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> OpenAI API request timed out"
            )

        except openai.APIConnectionError as e:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> Failed to connect to OpenAI API"
            )

        except openai.RateLimitError as e:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> OpenAI API request rate limit exceeded"
            )

        except openai.BadRequestError as e:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> Invalid request to OpenAI API"
            )

        except openai.AuthenticationError as e:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> Authentication error with OpenAI API"
            )

        except openai.APIError as e:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> An error returned from OpenAI API"
            )
        except openai.PermissionDeniedError:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> An error returned from OpenAI API"
            )
        except openai.ContentFilterFinishReasonError:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> ContentFilter error returned from OpenAI API"
            )
        except openai.LengthFinishReasonError:
            await openai_error_embed_handler(
                interaction=interaction,
                e=e,
                title="<a:CrossRed:1274034371724312646> An error returned from OpenAI API"
            )


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_cluster = self.bot.get_cluster()


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await initialize_assistants(self.db_cluster)


    @app_commands.command(name="chatgpt", description="Interact with the assistant.")
    @app_commands.describe(attachment="File to upload (optional).")
    async def chatgpt(self, interaction: discord.Interaction, attachment: Optional[discord.Attachment] = None):
        """
        Command to initiate ChatGPT interaction.
        """
        database = self.db_cluster["chatgpt"]
        channels_collection = database["discord_channels"]
        files_collection = database["files"]
        await interaction.response.send_modal(ChatGPTModal(db_cluster=self.db_cluster))
        if attachment:
            channel_id = interaction.channel.id
            user_id = interaction.user.id
            guild_id = interaction.guild.id if interaction.guild else None
            is_thread = isinstance(interaction.channel, discord.Thread)

            # Determine access level
            access_level = await get_access_level(self.db_cluster, interaction, user_id, guild_id)
            assistant_id = await get_assistant_by_access_level(self.db_cluster, access_level)
            await get_or_create_channel_entry(self.db_cluster, channel_id, guild_id, assistant_id, is_thread)

            # Create a temporary file
            local_path = await save_attachment_temporarily(attachment)
            try:
                # Upload file to OpenAI
                openai_file = await upload_file_to_openai(local_path)

                # Record file in MongoDB
                file_data = {
                    "channel_id": channel_id,
                    "filename": attachment.filename,
                    "local_path": local_path,
                    "file_id": openai_file.id
                }
                await files_collection.insert_one(file_data)

                # Update channel entry in MongoDB
                await channels_collection.update_one(
                    {"channel_id": channel_id},
                    {"$push": {"attachments": file_data}}
                )

            finally:
                # Ensure the temporary file is deleted after use
                if os.path.exists(local_path):
                    os.remove(local_path)


    async def reset_chat(self, interaction: Interaction, type: str, channel_id: str, guild_id: str = None, is_thread = False):
        """
        Clear stored chat messages in MongoDB.
        """
        database = self.db_cluster["chatgpt"]
        channels_collection = database["discord_channels"]
        query = {"guild_id": guild_id, "channel_id": channel_id, "is_thread": is_thread}

        if type == "channel":
            # Check if any records exist on the channel
            channel_records_exist = await channels_collection.find_one(query)
    
            if not channel_records_exist:
                return [f"<a:CrossRed:1274034371724312646> No **chat history** found on <#{interaction.channel.id}>.", False]

            await channels_collection.delete_one(query)
            await channels_collection.delete_one(query)

            if isinstance(interaction.channel, discord.DMChannel) or guild_id is None:
                return [f"**Chat history** reset for <#{interaction.channel.id}>.", True]    # channel.mention doesn't work for discord.DMChannel objects
            
            return [f"**Chat history** reset for {interaction.channel.mention} in **current server**.", True]
        
        elif type == "thread":
            if not isinstance(interaction.channel, discord.Thread):
                return [f"<a:CrossRed:1274034371724312646> <#{interaction.channel.id}> is **not a thread**.", False]    # channel.mention doesn't work for discord.DMChannel objects
            
            # Check if any records exist on the channel
            channel_records_exist = await channels_collection.find_one(query)
    
            if not channel_records_exist:
                return [f"<a:CrossRed:1274034371724312646> No **chat history** found on <#{interaction.channel.id}>.", False]

            await channels_collection.delete_one(query)
            await channels_collection.delete_one(query)
            
            return [f"**Chat history** reset for {interaction.channel.mention} in **current thread**.", True]
        
        elif type == "server":
            if isinstance(interaction.channel, discord.DMChannel) or guild_id is None:
                return [f"<a:CrossRed:1274034371724312646> <#{interaction.channel.id}> is **not belongs to** a **server**.", False]
            
            # Check if any records exist on the server
            server_records_exist = await channels_collection.find_one({"guild_id": guild_id})
            
            if not server_records_exist:
                return [f"<a:CrossRed:1274034371724312646> No **chat history** found on **this server**.", False]

            await channels_collection.delete_many({"guild_id": guild_id})
            await channels_collection.delete_many({"guild_id": guild_id})
            return ["**Chat history** reset for **this server**.", True]
        
        elif type == "all":
            # Check if any records exist globally
            all_records_exist = await channels_collection.find_one({})
    
            if not all_records_exist:
                return ["<a:CrossRed:1274034371724312646> No **chat history** found on **all server(s), channel(s) or thread(s)**.", False]
    
            # Delete all records
            await channels_collection.delete_many({})
            await channels_collection.delete_many({})
            return ["All chat history has been reset.", True]
        
        else:
            raise RuntimeError("An unexpected error occurred while resetting chat history.")


    # Clear chat history in ChatGPT
    @app_commands.command(name="resetgpt", description="Clear chat history in ChatGPT")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(type="Reset options")
    @app_commands.choices(type=[
        app_commands.Choice(name="Reset for current channel", value="channel"),
        app_commands.Choice(name="Reset for current thread", value="thread"),
        app_commands.Choice(name="Reset for current server", value="server"),
        app_commands.Choice(name="Reset for all channel(s) and server(s)", value="all")
    ])
    async def resetgpt(self, interaction: Interaction, type: app_commands.Choice[str]):
        """Reset ChatGPT history based on selected scope."""
        
        if not await self.bot.is_owner(interaction.user) and type.value == "all":   # "Reset all" restricted to bot owner only
            return await interaction.response.send_message(NotBotOwnerError())
        
        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id
        is_thread = isinstance(interaction.channel, discord.Thread)
        reset_result = await self.reset_chat(interaction, type.value, channel_id, guild_id, is_thread)
        reset_embed = Embed(title="", color=interaction.user.color) if reset_result[1] else Embed(title="", color=discord.Color.red())
        reset_embed.add_field(name="", value=reset_result[0], inline=False)
        
        await interaction.response.send_message(embed=reset_embed, ephemeral=True)
        

# ----------</ChatGPT>----------


async def setup(bot):
    await bot.add_cog(ChatGPT(bot))





