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

# Chat storage
chat_messages = {"DM": {}, "Guild": {}}
chat_history = {"DM": {}, "Guild": {}}

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


class ChatGPTModal(Modal, title="Talk to our AI assistant"):
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


    async def on_submit(self, interaction: Interaction):
        """Process and handle the modal submission."""
        channel_id = interaction.channel.id
        guild_id = interaction.guild.id if interaction.guild else None
        context = "Guild" if interaction.guild else "DM"
        
        if isinstance(interaction.channel, discord.DMChannel):
            messages = chat_messages[context].setdefault(channel_id, [])    # DM messages
            history = chat_history[context].setdefault(channel_id, [])
        
        elif guild_id:
            messages = chat_messages[context].setdefault(guild_id, {}).setdefault(channel_id, [])   # Guild messages
            history = chat_history[context].setdefault(guild_id, {}).setdefault(channel_id, [])
        
        else:
            raise NotImplementedError()    # Rare cases

        # Initialize interaction response
        await interaction.response.defer()
        wait_message = await interaction.followup.send("<a:LoadingCustom:1295993639641812992> *Waiting for GPT to respond...*", wait=True)
        
        if len(history) > 60:
            ChatGPT.reset_chat(interaction, "channel", channel_id, guild_id)

        prompt_text = self.custom_prompt.value or GPT_MODEL_CONFIG["system_message"]
        messages.append({"role": "system", "content": prompt_text})
        messages.append({"role": "user", "content": self.content.value})

        response = await self.get_response_from_gpt(interaction, messages)
        
        if response is None:
            return await wait_message.edit(content="<a:CrossRed:1274034371724312646> An error occured while communicating with Azure OpenAI API.")
        
        history.append({"role": "assistant", "content": response})
        quote = f"> {interaction.user.mention}: **{self.content.value}**{discord.utils.escape_markdown(' ')}"
        edited_response = f"{quote}\n{discord.utils.escape_markdown(' ')}\n{response}"
        
        formatted_responses = format_message(edited_response)
        
        for msg in formatted_responses:
            await interaction.followup.send(msg)
        
        await wait_message.delete()

class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def reset_chat(interaction: Interaction, type: str, channel_id: int, guild_id: int = None):
        """Clear stored chat messages and history based on reset scope. Returning as [message: str, status: bool]"""
        if type == "channel":
            
            if isinstance(interaction.channel, discord.DMChannel):
                
                if chat_messages["DM"].get(channel_id) and chat_history["DM"].get(channel_id):
                    chat_messages["DM"].pop(channel_id, None)
                    chat_history["DM"].pop(channel_id, None)
                    return [f"Chat history reset for <#{interaction.channel.id}>.", True]    # channel.mention doesn't work for discord.DMChannel objects
                
                else:
                    return [f"<a:CrossRed:1274034371724312646> No chat history for channel {interaction.channel.mention}.", False]
            
            if chat_messages["Guild"].get(guild_id, {}).get(channel_id) and chat_history["Guild"].get(guild_id, {}).get(channel_id):
                chat_messages["Guild"].get(guild_id, {}).pop(channel_id, None)
                chat_history["Guild"].get(guild_id, {}).pop(channel_id, None)
                return [f"Chat history reset for {interaction.channel.mention} in current server.", True]
            
            else:
                return [f"<a:CrossRed:1274034371724312646> No chat history for channel {interaction.channel.mention}.", False]
        
        elif type == "server":
            
            if isinstance(interaction.channel, discord.DMChannel):
                return [f"<a:CrossRed:1274034371724312646> <#{interaction.channel.id}> is not belongs to a server.", False]   # channel.mention doesn't work for discord.DMChannel objects
            
            if chat_messages["Guild"].get(guild_id) and chat_history["Guild"].get(guild_id):
                chat_messages["Guild"].pop(guild_id, None)
                chat_history["Guild"].pop(guild_id, None)
                return ["Chat history has been reset for current server.", True]
            
            else:
                return ["<a:CrossRed:1274034371724312646> No chat history for current server.", False]
        
        elif type == "all":
            
            if chat_messages["DM"] == {} and chat_messages["Guild"] == {} and chat_history["DM"] == {} and chat_history["Guild"] == {}:
                return ["<a:CrossRed:1274034371724312646> No chat history for all channel(s) and server(s).", False]
            
            chat_messages["DM"].clear()
            chat_messages["Guild"].clear()
            chat_history["DM"].clear()
            chat_history["Guild"].clear()
            
            return ["All chat history has been reset.", True]
        
        else:
            raise RuntimeError(f"An unexpected error occured while resetting ChatGPT.")


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
        await interaction.response.send_modal(ChatGPTModal())

# ----------</ChatGPT>----------

async def setup(bot):
    await bot.add_cog(ChatGPT(bot))
 
 