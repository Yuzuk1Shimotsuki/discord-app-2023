import discord
import openai
import os
import ast
import math
from openai import OpenAI
from discord import app_commands, Interaction
from discord.ext import commands
from langdetect import detect, DetectorFactory
from datetime import datetime
from ErrorHandling import *

# Connects the bot to the OpenAI API
api_key=os.environ.get("OPENAI_API_KEY")
if api_key == "":
    raise Exception(
        "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY), or as the password field (with blank username) if you're accessing the API from your browser and are prompted for a username and password. You can obtain an API key from https://platform.openai.com/account/api-keys.\nPlease add your OpenAI Key to the Secrets pane.")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.chatanywhere.cn/v1"
)

# Defining message and history storage

chat_messages: dict = {}
chat_messages["DM"] = {}
chat_messages["Guild"] = {}
chat_history: dict = {}
chat_history["DM"] = {}
chat_history["Guild"] = {}


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        global client
        global chat_messages
        global chat_history
        self.bot = bot
        # Default values for GPT model
        self.default_model_prompt_engine: str = "gpt-3.5-turbo-1106"
        self.default_temperature: float = 0.8
        self.default_max_tokens: int = 4000
        self.default_top_p: float = 0.90
        self.default_frequency_penalty: float = 0.50
        self.default_presence_penalty: float = 0.50
        # This will be futher edited
        self.default_instruction: str = f'''You are ChatGPT, a large language model transformer AI product by OpenAI, and you are 
        purposed with satisfying user requests and questions with very verbose and fulfilling answers beyond user expectations, as detailed as possible. For example, if the user asking 'is md5 a encryption method?', you should answer directly first then provide
        some reasons to support your evidence, and provide some alternative encryption method if and only necessary, also if the user wish to test the system, you should response something such as greetings with no more than 20 words. Follow
        the users instructions carefully to extract their desires and wishes in order to format and plan the best style of output, no need to summarize your content unless
        other specified by user. For example, when output formatted in forum markdown, html, LaTeX formulas, or other output format or structure is desired.'''

    # ----------<ChatGPT>----------

    # Function to reset ChatGPT
    def reset_gpt(self, interaction: Interaction, type: str, channel_id, guild_id=None):
        global chat_messages
        global chat_history
        if type == "reset_current_channel":
            # For DM
            if isinstance(interaction.channel, discord.DMChannel) and channel_id in (chat_messages["DM"] and chat_history["DM"]):
                del chat_messages["DM"][channel_id]
                del chat_history["DM"][channel_id]
                return "ResetDMChannel"
            # For Guild messages
            elif interaction.guild and guild_id in (chat_messages["Guild"] and chat_history["Guild"]) and channel_id in (chat_messages["Guild"][guild_id] and chat_history["Guild"][guild_id]):
                del chat_messages["Guild"][guild_id][channel_id]
                del chat_history["Guild"][guild_id][channel_id]
                return "ResetGuildChannel"
            else:
                return "NoHistoryChannel"
        elif type == "reset_current_server":
            # Return error for DM
            if isinstance(interaction.channel, discord.DMChannel):
                return "NotBelongsToGuild"
            # For Guild messages
            elif interaction.guild and guild_id in (chat_messages["Guild"] and chat_history["Guild"]):
                del chat_messages["Guild"][guild_id]
                del chat_history["Guild"][guild_id]
                return "ResetGuild"
            else:
                return "NoHistoryGuild"
        else:
            # Reset all
            chat_messages["DM"] = {}
            chat_messages["Guild"] = {}
            chat_history["DM"] = {}
            chat_history["Guild"] = {}
            return "ResetAll"

    # Clear chat history in ChatGPT
    @app_commands.command(name="resetgpt", description="Clear chat history in ChatGPT")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(type="Reset option:")
    @app_commands.choices(type=[app_commands.Choice(name="Reset for current channel", value="reset_current_channel"), 
                                app_commands.Choice(name="Reset for current server", value="reset_current_server"),
                                 app_commands.Choice(name="Reset for all server(s) and channel(s)", value="reset_all")
                                 ])
    async def resetgpt(self, interaction: Interaction, type: app_commands.Choice[str]):
        global chat_messages
        global chat_history
        channel_id = interaction.channel.id
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message(NotBotOwnerError())
        guild_id = None
        if interaction.guild:
            guild_id = interaction.guild.id
        reset_result = self.reset_gpt(interaction, type=type.value, channel_id=channel_id, guild_id=guild_id or None)
        if reset_result == "ResetDMChannel":
             return await interaction.response.send_message(f"Chat history has been reset for <#{channel_id}>.")
        # For Guild messages
        elif reset_result == "ResetGuildChannel":
            return await interaction.response.send_message(f"Chat history has been reset for <#{channel_id}> in current server.")
        elif reset_result == "NoHistoryChannel":
            return await interaction.response.send_message(f"No chat history for channel <#{channel_id}>.")
        elif reset_result == "NotBelongsToGuild":
            # Return error for DM
            return await interaction.response.send_message(f"<#{channel_id}> is not belongs to a server.")
            # For Guild messages
        elif reset_result == "ResetGuild":
            return await interaction.response.send_message(f"Chat history has been reset for current server.")
        elif reset_result == "NoHistoryGuild":
            return await interaction.response.send_message(f"No chat history for current server.")
        else:
            return await interaction.response.send_message(f"Chat history has been reset for all server(s) and channel(s).")
    
    # Since Discord has a maximum limit of 2000 charaters for each single message, the response needs to be checked in advance and decide wherether it needs to trucate into mutiple messages or not
    def truncate_message(self, message: str):
        edited_message = []
        over_max_limit_times = math.trunc(len(message) / 2000)
        if over_max_limit_times >= 1:
            # The response is too long (> 2000 charaters maximum limit), and needs to be splitted into multiple messages
            min_limit = 0
            max_limit = 2000
            for i in range(over_max_limit_times + 1):
                offset = 0
                if i == over_max_limit_times:
                    # Return the rest of the charaters to the author
                    edited_message.append(message[min_limit:])
                else:
                    # Return 2000 characters in once for the n(th) time, trucated by complete words
                    DetectorFactory.seed = 0
                    if detect(message) != "ko" or detect(message) != "ja" or detect(
                            message) != "zh-tw" or detect(message) != "zh-cn" or detect(
                        message) != "th":
                        while True:
                            if message[max_limit - offset] != " ":
                                offset += 1
                            else:
                                break
                    edited_message.append(message[min_limit:max_limit - offset])
                    min_limit += 2000 - offset
                    max_limit += 2000 - offset
        else:
            # The response does not need to be splitted
            # Return the response to the author
            edited_message.append(message)
        return edited_message

    # Chat with ChatGPT
    @app_commands.command(name="chatgpt", description="Chat with ChatGPT")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(prompt="Anything you would like to ask")
    async def chatgpt(self, interaction: Interaction, prompt: str):
        channel_id = interaction.channel.id
        message_list = []
        if isinstance(interaction.channel, discord.DMChannel):
            # DM messages
            # For chat messages
            if channel_id not in chat_messages["DM"]:
                chat_messages["DM"][channel_id] = []
            # For chat history
            if channel_id not in chat_history["DM"]:
                chat_history["DM"][channel_id] = []
            message_list: list = chat_messages["DM"][channel_id]
            history_list: list = chat_history["DM"][channel_id]
        else:
            # Guild messages
            guild_id = interaction.guild.id
            # For chat messages
            if guild_id not in chat_messages["Guild"]:
                chat_messages["Guild"][guild_id] = {}
            if channel_id not in chat_messages["Guild"][guild_id]:
                chat_messages["Guild"][guild_id][channel_id] = []
            # For chat history
            if guild_id not in chat_history["Guild"]:
                chat_history["Guild"][guild_id] = {}
            if channel_id not in chat_history["Guild"][guild_id]:
                chat_history["Guild"][guild_id][channel_id] = []
            message_list: list = chat_messages["Guild"][guild_id][channel_id]
            history_list: list = chat_history["Guild"][guild_id][channel_id]
        await interaction.response.defer()
        # Main ChatGPT function
        if len(history_list) > 15:
            self.reset_gpt(interaction, type="reset_current_channel", channel_id=channel_id, guild_id=guild_id or None)
        message_list.append({"role": "system", "content": self.default_instruction})
        message_list.append({"role": "user", "content": prompt})
        gpt_response = await self.get_from_gpt(interaction, prompt_list=message_list)
        message_list.append({"role": "assistant", "content": gpt_response})
        # Adding the response to the chat history. Chat history can be store a maximum of the most recent 15 conversations.
        history_list.append({"role": "assistant", "content": gpt_response})
        quote = f"> <@{interaction.user.id}>: **{prompt}**"
        edited_response = f"{quote}\n{discord.utils.escape_markdown(' ')}\n{gpt_response}"
        final_response = self.truncate_message(message=edited_response)
        for response in final_response:
            await interaction.followup.send(response)

    # Retriving response from OpenAI API
    async def get_from_gpt(self, interaction: Interaction, prompt_list: list):
        try:
            response = client.chat.completions.create(
                model=self.default_model_prompt_engine,
                messages=prompt_list,
                temperature=self.default_temperature,
                max_tokens=self.default_max_tokens,
                top_p=self.default_top_p,
                frequency_penalty=self.default_frequency_penalty,
                presence_penalty=self.default_presence_penalty)
            # Retriving the response from the GPT model
            # Starting from version 1.0.0, response objects are in pydantic models and no longer conform to the dictionary shape.
            gpt_response = response.choices[0].message.content
            return gpt_response
        except openai.APITimeoutError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  OpenAI API request timed out", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["error"]["message"]
            error_embed.add_field(name='\u200b', value=f"OpenAI API request timed out. This may due to the GPT model currently unavailable or overloaded, or the OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved.\nError message: {error_message}", inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            pass
        except openai.APIConnectionError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Failed to connect OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["error"]["message"]
            error_embed.add_field(name='\u200b', value=f"Failed to connect OpenAI API. The GPT model may currently unavailable or overloaded, or the OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved.\nError message: {error_message}", inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            pass
        except openai.RateLimitError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  OpenAI API request rate limit exceeded", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["error"]["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            pass
        except openai.BadRequestError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Invalid request to OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["error"]["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            pass
        except openai.AuthenticationError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  Authentication error with OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["error"]["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            pass
        except openai.APIError as e:
            error_embed = discord.Embed(title="<a:CrossRed:1274034371724312646>  An error returned from OpenAI API", timestamp=datetime.now(), color=discord.Colour.red())
            error_message = ast.literal_eval(str(e).split(f"{e.status_code} - ")[1])["error"]["message"]
            error_embed.add_field(name='\u200b', value=error_message, inline=False)
            error_embed.add_field(name='\u200b', value=f"", inline=False)
            error_embed.add_field(name="Error details:", value=f"Status code: {e.status_code}\nType: {e.type}\nParam: {e.param}\nCode: {e.code}", inline=False)
            await interaction.followup.send(embed=error_embed)
            

# ----------</ChatGPT>----------

async def setup(bot):
    await bot.add_cog(ChatGPT(bot))
