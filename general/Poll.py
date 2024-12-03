import discord
import asyncio
from discord import app_commands, Interaction, Poll, PollAnswer, PollLayoutType, PollMedia
from discord.errors import NotFound
from discord.ext import commands
from discord.utils import get
from datetime import datetime, timedelta
from typing import Optional
from errorhandling.ErrorHandling import *

most_recent_poll_message = {}


class PollNew(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot


    # Getting required message ID from user input
    async def get_message_id(self, message: str):
        try:
            if message.startswith("https://discord.com/channels/"):
                # URL
                url_list = message.split("/")
                message_id = int(url_list[-1])

            else:
                # ID
                message_id = int(message)

            return message_id
        
        except ValueError:
            # The type of message user provided was not a valid type
            return None


    # Creates a new poll
    @app_commands.command(description='Creates a poll')
    @app_commands.choices(duration=[    # in hours
        app_commands.Choice(name="1 hour", value=str(1)),   # 1 hour
        app_commands.Choice(name="4 hours", value=str(4)),  # 4 hours
        app_commands.Choice(name="8 hours", value=str(8)),  # 8 hours
        app_commands.Choice(name="3 days", value=str(3 * 24)),  # 72 hours
        app_commands.Choice(name="1 week", value=str(7 * 24)),  # 168 hours
        app_commands.Choice(name="3 weeks", value=str(3 * (7 * 24))),   # 504 hours
        app_commands.Choice(name="(Custom)", value="custom")
        ])
    @app_commands.describe(question="Question of the poll")
    @app_commands.describe(answers="Answers of the poll (Seperated with a comma e.g. answer1, answer2, ... , answer9, answer10)")
    @app_commands.describe(duration="Duration of the poll. Choose '(Custom)' if you want to customize.")
    @app_commands.describe(duration="Custom duration of the poll (in hours). Leave this blank if 'duration' has been set properly.")
    @app_commands.describe(multiple="Allow multiple answers")
    async def poll(self, interaction: Interaction, question: str, answers: str, duration: app_commands.Choice[str], custom_duration: Optional[app_commands.Range[int, 1, None]] = None, multiple: bool = False):
        global most_recent_poll_message
        PollSuccessEmbed = discord.Embed(title="Success!", color=discord.Colour.green())
        PollErrorEmbed = discord.Embed(title="Error", color=discord.Colour.red())
        guild_id = interaction.guild.id

        if (duration.value == "custom" and custom_duration is None) or (duration.value != "custom" and custom_duration is not None):
            PollErrorEmbed.add_field(name=f"", value=f"Please enter a vaild duration for the poll!", inline=False)
            return await interaction.response.send_message(embed=PollErrorEmbed)
        
        if duration.value == "custom":
            vaild_duration = custom_duration

        else:
            vaild_duration = int(duration.value)

        total_hours = timedelta(hours=vaild_duration)
        answer_list = answers.split(", ")

        if len(answer_list) > 10:
            PollErrorEmbed.add_field(name=f"", value=f"Looks like the number of options you entered exceeded the maximum limit :thinking: ... (**{len(answer_list)}** out of **10**)", inline=False)
            return await interaction.response.send_message(embed=PollErrorEmbed)
        new_poll = Poll(question=question, duration=total_hours, multiple=multiple, layout_type=PollLayoutType.default)

        for poll_answer in answer_list:
            new_poll.add_answer(text=poll_answer, emoji=None)

        if guild_id in most_recent_poll_message:
            del most_recent_poll_message[guild_id]

        PollSuccessEmbed.add_field(name=f"", value=f"The poll has been created.", inline=False)
        await interaction.response.send_message(embed=PollSuccessEmbed, ephemeral=True, silent=True, delete_after=1.5)
        most_recent_poll_message[guild_id] = await interaction.channel.send(poll=new_poll)


    # Since adding and removing answer from the poll were not suppported in discord API currently, those operations were ignored.

    # End and shows the result of the poll
    @app_commands.command(description='Terminates and show results of the poll')
    @app_commands.describe(poll_message="The ID of message. Defaults to the most recent poll.")
    async def endpoll(self, interaction: Interaction, poll_message: Optional[str] = None):
        global most_recent_poll_message
        await interaction.response.defer()
        PollSuccessEmbed = discord.Embed(title="Success!", color=discord.Colour.green())
        PollErrorEmbed = discord.Embed(title="Error", color=discord.Colour.red())
        guild_id = interaction.guild.id
        poll_to_edit = None

        if poll_message is None and guild_id in most_recent_poll_message:  # Returns if no "poll_message" were specified and self.most_recent_poll_message[guild_id] exsist.
            poll_to_edit = most_recent_poll_message[guild_id]

        elif poll_message is not None:  # Returns if "poll_message" were specified.
            message_id = await self.get_message_id(poll_message)

            for text_channel in interaction.guild.text_channels:
                if poll_to_edit is None:
                    try:
                        poll_to_edit = await text_channel.fetch_message(message_id)

                    except NotFound:
                        pass

                else:
                    break

        else:   # Returns if no "poll_message" were specified and self.most_recent_poll_message[guild_id] does not exsist.
            PollErrorEmbed.add_field(name=f"", value=f"There is currently no vaild polls on this server, or `poll_message` has not been specified yet.", inline=False)
            return await interaction.followup.send(embed=PollErrorEmbed)
        
        if poll_to_edit is None:
            PollErrorEmbed.add_field(name=f"", value=f"The poll you wanted to terminate were not created on this server!", inline=False)
            return await interaction.followup.send(embed=PollErrorEmbed)
        
        elif poll_to_edit.poll is None:
            PollErrorEmbed.add_field(name=f"", value=f"There is no poll attached on this message!", inline=False)
            return await interaction.followup.send(embed=PollErrorEmbed)
        
        elif poll_to_edit.poll.is_finalised():
            PollErrorEmbed.add_field(name=f"", value=f"The poll has been already terminated!", inline=False)
            return await interaction.followup.send(embed=PollErrorEmbed)
        
        else:
            await poll_to_edit.end_poll()
            PollSuccessEmbed.add_field(name=f"", value=f"The poll has been terminated.", inline=False)
            msg = await interaction.followup.send(embed=PollSuccessEmbed, ephemeral=True, silent=True)
            await asyncio.sleep(1.5)
            await msg.delete()
        

async def setup(bot):
    await bot.add_cog(PollNew(bot))
