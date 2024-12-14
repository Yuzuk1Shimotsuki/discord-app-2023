import discord
import openai
import os
import ast
import math
from dotenv import load_dotenv
from openai import AzureOpenAI
from discord import app_commands, Interaction, Embed, TextStyle
from discord.ext import commands
from discord.ui import Modal, TextInput
from langdetect import detect, DetectorFactory
from datetime import datetime
from errorhandling.ErrorHandling import *

load_dotenv()

# Azure OpenAI API Setup
azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_api_endpoint = f"{os.getenv('AZURE_OPENAI_ENDPOINT')}?api-version={azure_api_version}"

if azure_api_key is None:
    raise openai.AuthenticationError("You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY), or as the password field (with blank username) if you're accessing the API from your browser and are prompted for a username and password. You can obtain an API key from https://platform.openai.com/account/api-keys. \nPlease add your Azure OpenAI Key to the environment variables.")

client = AzureOpenAI(api_key=azure_api_key, api_version=azure_api_version, azure_endpoint=azure_api_endpoint)

# GPT Model Defaults
GPT_MODEL_CONFIG = {
    "model": "gpt4o",
    "temperature": 0.8,
    "max_tokens": 4096,
    "top_p": 0.90,
    "frequency_penalty": 0.50,
    "presence_penalty": 0.50,
    "system_message":   # This will be futher edited
    f'''You are ChatGPT, a large language model transformer AI product by OpenAI, and you are 
purposed with satisfying user requests and questions with very verbose and fulfilling answers beyond user expectations, as detailed as possible. For example, if the user asking 'is md5 a encryption method?', you should answer directly first then provide
some reasons to support your evidence, and provide some alternative encryption method if and only necessary, also if the user wish to test the system, you should response something such as greetings with no more than 20 words. Follow
the users instructions carefully to extract their desires and wishes in order to format and plan the best style of output, no need to summarize your content unless
other specified by user. For example, when output formatted in forum markdown, html, LaTeX formulas, or other output format or structure is desired.
    '''
}

def format_message(message: str) -> list:
    """Format and split a message into chunks that adhere to Discord's 2000 character limit."""
    message = message.replace("######", "###").replace("#####", "###").replace("####", "###")
    parts = []
    min_limit = 0
    max_limit = 2000

    for i in range(math.ceil(len(message) / max_limit)):
        offset = 0
        if i < len(message) // max_limit:
            DetectorFactory.seed = 0
            
            if detect(message) not in ["ko", "ja", "zh-tw", "zh-cn", "th"]:
                
                while max_limit - offset > 0 and message[max_limit - offset - 1] != " ":
                    offset += 1

        parts.append(message[min_limit:max_limit - offset].strip())
        min_limit += 2000 - offset
        max_limit += 2000 - offset
    
    return parts


class ChatGPTModal(Modal):
    def __init__(self, db):
        self.db = db    # Connect to MongoDB
        super().__init__(title="Talk to our AI assistant")

    custom_prompt = TextInput(
        label="Custom Prompt",
        placeholder="Your prompt here...",
        style=TextStyle.paragraph,
        max_length=1500,
        required=False
    )
    content = TextInput(
        label="Content",
        placeholder="Your content here...",
        style=TextStyle.paragraph,
        max_length=4000,
        required=True
    )


    # ----------<ChatGPT>----------


    async def get_response_from_gpt(self, interaction: Interaction, prompt_list: list):
        """Retrieve GPT response from Azure OpenAI API, handling errors gracefully."""
        try:
            response = client.chat.completions.create(
                model=GPT_MODEL_CONFIG["model"],
                messages=prompt_list,
                temperature=GPT_MODEL_CONFIG["temperature"],
                max_tokens=GPT_MODEL_CONFIG["max_tokens"],
                top_p=GPT_MODEL_CONFIG["top_p"],
                frequency_penalty=GPT_MODEL_CONFIG["frequency_penalty"],
                presence_penalty=GPT_MODEL_CONFIG["presence_penalty"]
            )
            return response.choices[0].message.content
        
        # Handling expections from API errors
        except openai.APITimeoutError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Azure OpenAI API request timed out", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["message"]
            error_embed.add_field(name='\u200b', value=f"Azure OpenAI API request timed out. This may due to the GPT model currently unavailable or overloaded, or the Azure OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved.\nError message: {error_message}", inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            return None
        
        except openai.APIConnectionError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Failed to connect Azure OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["message"]
            error_embed.add_field(name='\u200b', value=f"Failed to connect Azure OpenAI API. The GPT model may currently unavailable or overloaded, or the Azure OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved.\nError message: {error_message}", inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            return None
        
        except openai.RateLimitError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Azure OpenAI API request rate limit exceeded", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            return None
        
        except openai.BadRequestError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Invalid request to Azure OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            return None
        
        except openai.AuthenticationError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Authentication error with Azure OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            return None
        
        except openai.APIError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  An error returned from Azure OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            return None


    # Action after submitting the modal
    async def on_submit(self, interaction: Interaction):
        """Process and handle the modal submission."""
        database = self.db.chatgpt
        chat_messages_collection = database["messages"]
        chat_history_collection = database["history"]
        channel_id = interaction.channel.id
        guild_id = interaction.guild.id if interaction.guild else None
        context = "Guild" if interaction.guild else "DM"

        # Initialize interaction response
        await interaction.response.defer()
        wait_message = await interaction.followup.send("<a:LoadingCustom:1295993639641812992> *Waiting for GPT to respond...*", wait=True)

        # Fetch or initialize chat history from MongoDB
        query = {"context": context, "guild_id": guild_id, "channel_id": channel_id}
        chat_messages = await chat_messages_collection.find_one(query) or {"messages": []}
        history = await chat_history_collection.find_one(query) or {"history": []}

        # Reset chat history if too long
        if len(history.get("history", [])) > 60:
            ChatGPT.reset_chat(interaction, "channel", channel_id, guild_id)

        # Prepare messages
        prompt_text = self.custom_prompt.value or GPT_MODEL_CONFIG["system_message"]
        chat_messages["messages"].append({"role": "system", "content": prompt_text})
        chat_messages["messages"].append({"role": "user", "content": self.content.value})

        response = await self.get_response_from_gpt(interaction, chat_messages["messages"])
        if response is None:
            return await wait_message.edit(content="<a:CrossRed:1274034371724312646> An error occurred while communicating with Azure OpenAI API.")

        # Save response to MongoDB
        history["history"].append({"role": "assistant", "content": response})
        await chat_history_collection.update_one(query, {"$set": history}, upsert=True)
        await chat_messages_collection.update_one(query, {"$set": chat_messages}, upsert=True)

        # Format and send response
        quote = f"> {interaction.user.mention}: **{self.content.value}**{discord.utils.escape_markdown(' ')}"
        edited_response = f"{quote}\n{discord.utils.escape_markdown(' ')}\n{response}"
        
        formatted_responses = format_message(edited_response)
        
        for msg in formatted_responses:
            await interaction.followup.send(msg)
        
        await wait_message.delete()


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cluster()


    async def reset_chat(self, interaction: Interaction, type: str, channel_id: str, guild_id: str = None):
        """Clear stored chat messages and history in MongoDB."""
        query = {"context": "Guild" if guild_id else "DM", "guild_id": guild_id, "channel_id": channel_id}
        database = self.db.chatgpt
        chat_messages_collection = database["messages"]
        chat_history_collection = database["history"]

        if type == "channel":
            # Check if any records exist on the channel
            channel_records_exist = await chat_messages_collection.find_one(query) and await chat_history_collection.find_one(query)
    
            if not channel_records_exist:
                return [f"<a:CrossRed:1274034371724312646> No **chat history** found on <#{interaction.channel.id}>.", False]

            await chat_messages_collection.delete_one(query)
            await chat_history_collection.delete_one(query)

            if isinstance(interaction.channel, discord.DMChannel) or guild_id is None:
                return [f"**Chat history** reset for <#{interaction.channel.id}>.", True]    # channel.mention doesn't work for discord.DMChannel objects
            
            return [f"**Chat history** reset for {interaction.channel.mention} in **current server**.", True]
        
        elif type == "server":
            if isinstance(interaction.channel, discord.DMChannel) or guild_id is None:
                return [f"<a:CrossRed:1274034371724312646> <#{interaction.channel.id}> is **not belongs to** a **server**.", False]
            
            # Check if any records exist on the server
            server_records_exist = await chat_messages_collection.find_one({"context": "Guild", "guild_id": guild_id}) and await chat_history_collection.find_one({"context": "Guild", "guild_id": guild_id})
            
            if not server_records_exist:
                return [f"<a:CrossRed:1274034371724312646> No **chat history** found on **this server**.", False]

            await chat_messages_collection.delete_many({"context": "Guild", "guild_id": guild_id})
            await chat_history_collection.delete_many({"context": "Guild", "guild_id": guild_id})
            return ["**Chat history** reset for **this server**.", True]
        
        elif type == "all":
            # Check if any records exist globally
            all_records_exist = await chat_messages_collection.find_one({}) and await chat_history_collection.find_one({})
    
            if not all_records_exist:
                return ["<a:CrossRed:1274034371724312646> No **chat history** found on **all server(s) and channel(s)**.", False]
    
            # Delete all records
            await chat_messages_collection.delete_many({})
            await chat_history_collection.delete_many({})
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
        app_commands.Choice(name="Reset for current server", value="server"),
        app_commands.Choice(name="Reset for all channel(s) and server(s)", value="all")
    ])
    async def resetgpt(self, interaction: Interaction, type: app_commands.Choice[str]):
        """Reset ChatGPT history based on selected scope."""
        
        if not await self.bot.is_owner(interaction.user) and type.value == "all":   # "Reset all" restricted to bot owner only
            return await interaction.response.send_message(NotBotOwnerError())
        
        guild_id = interaction.guild.id if interaction.guild else None
        channel_id = interaction.channel.id
        reset_result = self.reset_chat(interaction, type.value, channel_id, guild_id)
        reset_embed = Embed(title="", color=interaction.user.color) if reset_result[1] else Embed(title="", color=discord.Color.red())
        reset_embed.add_field(name="", value=reset_result[0], inline=False)
        
        await interaction.response.send_message(embed=reset_embed, ephemeral=True)


    # Chat with ChatGPT
    @app_commands.command(name="chatgpt", description="Chat with ChatGPT")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def chatgpt(self, interaction: Interaction):
        """Launch the ChatGPT modal for user interaction."""
        await interaction.response.send_modal(ChatGPTModal(db=self.db))


# ----------</ChatGPT>----------


async def setup(bot):
    await bot.add_cog(ChatGPT(bot))

