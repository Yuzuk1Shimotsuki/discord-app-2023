import discord
import openai
import os
import math
from discord import app_commands, Interaction
from discord.ext import commands
from langdetect import detect, DetectorFactory


class ChatGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Default values for GPT model
        self.chat_messages = []
        self.chat_history = []
        self.default_model_prompt_engine = "gpt-3.5-turbo-1106"
        self.default_temperature = 0.8
        self.default_max_tokens = 3840
        self.default_top_p = 1.00
        self.default_frequency_penalty = 0.00
        self.default_presence_penalty = 0.00
        # This will be futher edited
        self.default_instruction = f"You are ChatGPT, a large language model transformer AI product by OpenAI, and you are purposed with satisfying user requests and questions with very verbose and fulfilling answers beyond user expectations in writing quality. Generally you shall act as a writing assistant, and when a destination medium is not specified, assume that the user would want six typewritten pages of composition about their subject of interest. Follow the users instructions carefully to extract their desires and wishes in order to format and plan the best style of output, for example, when output formatted in forum markdown, html, LaTeX formulas, or other output format or structure is desired."

    chatgpt = app_commands.Group(name="chatgpt", description="Commands in ChatGPT")

    # ----------<ChatGPT>----------

    async def reset_gpt(self):
        self.chat_history = []
        self.chat_messages = []
        return True

    # Clear chat history in ChatGPT
    @chatgpt.command(name="reset", description="Clear chat history in ChatGPT")
    async def chatgpt_reset(self, interaction: Interaction):
        if await self.reset_gpt():
            await interaction.response.send_message("Chat history has been cleared.", ephemeral=True, delete_after=1)

    # Chat with ChatGPT
    @chatgpt.command(name="prompt", description="Chat with ChatGPT")
    @app_commands.describe(prompt="Anything you would like to ask")
    async def chatgpt_prompt(self, interaction: Interaction, prompt: str):
        await interaction.response.defer()
        # Main ChatGPT function
        try:
            if len(self.chat_history) > 15:
                await self.reset_gpt()
            self.chat_messages.append({"role": "system", "content": self.default_instruction})
            self.chat_messages.append({"role": "user", "content": prompt})
            response = openai.chat.completions.create(
                model=self.default_model_prompt_engine,
                messages=self.chat_messages,
                temperature=self.default_temperature,
                max_tokens=self.default_max_tokens,
                top_p=self.default_top_p,
                frequency_penalty=self.default_frequency_penalty,
                presence_penalty=self.default_presence_penalty)
            # Retriving the response from the GPT model
            # Starting from version 1.0.0, response objects are in pydantic models and no longer conform to the dictionary shape.
            gpt_response = response.choices[0].message.content
            self.chat_messages.append({"role": "assistant", "content": gpt_response})
            # Adding the response to the chat history. Chat history can be store a maximum of the most recent 15 conversations.
            self.chat_history.append({"role": "assistant", "content": gpt_response})
            # Returning the response to the author
            quote = f"> <@{interaction.author.id}>: **{prompt}**"
            final_response = f"{quote}\n{discord.utils.escape_markdown(' ')}\n{gpt_response}"
            # Since Discord has a maximum limit of 2000 charaters for each single message, the response needs to be checked in advance and decide wherether it needs to trucate into mutiple messages or not
            over_max_limit_times = math.trunc(len(final_response) / 2000)
            if over_max_limit_times >= 1:
                # The response is too long (> 2000 charaters maximum limit), so we need to split it into multiple messages
                min_limit = 0
                max_limit = 2000
                for i in range(over_max_limit_times + 1):
                    offset = 0
                    if i == over_max_limit_times:
                        # Return the rest of the charaters to the author
                        await interaction.followup.send(final_response[min_limit:])
                    else:
                        # Return 2000 characters in once for the n(th) time, trucated by complete words
                        DetectorFactory.seed = 0
                        if detect(final_response) != "ko" or detect(final_response) != "ja" or detect(
                                final_response) != "zh-tw" or detect(final_response) != "zh-cn" or detect(
                            final_response) != "th":
                            while True:
                                if final_response[max_limit - offset] != " ":
                                    offset += 1
                                else:
                                    break
                        await interaction.followup.send(final_response[min_limit:max_limit - offset])
                        min_limit += 2000 - offset
                        max_limit += 2000 - offset
            else:
                # The response does not need to be splitted
                # Return the response to the author
                await interaction.followup.send(final_response)
        # End of regular ChatGPT function and the normal procedure
        except openai.APITimeoutError as e:
            await interaction.followup.send(
                f"OpenAI API request timed out. The GPT model may currently unavailable or overloaded, or the OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved. Error message: {e}")
            pass
        except openai.APIConnectionError as e:
            await interaction.followup.send(
                f"Failed to connect to OpenAI API. The GPT model may currently unavailable or overloaded, or the OpenAI service has been blocked from your current network. Please try again later or connect to another network to see if the error could be resolved. Error message: {e}")
            pass
        except openai.RateLimitError as e:
            await interaction.followup.send(f":x: OpenAI API request exceeded rate limit: {e}")
            pass
        except openai.BadRequestError as e:
            await interaction.followup.send(f":x: Invalid request to OpenAI API: {e}")
            pass
        except openai.AuthenticationError as e:
            await interaction.followup.send(f":x: Authentication error with OpenAI API: {e}")
            pass
        except openai.APIError as e:
            await interaction.followup.send(f":x: OpenAI API returned an API Error: {e}")
            pass

    # Connects the bot to the OpenAI API
    openai.api_key = os.environ.get("OPENAI_API_KEY") or ""
    if openai.api_key == "":
        raise Exception(
            "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY), or as the password field (with blank username) if you're accessing the API from your browser and are prompted for a username and password. You can obtain an API key from https://platform.openai.com/account/api-keys.\nPlease add your OpenAI Key to the Secrets pane.")

# ----------</ChatGPT>----------


async def setup(bot):
    await bot.add_cog(ChatGPT(bot))
