import discord
from discord import app_commands, Interaction, Activity, Game, Streaming
from discord.ext import commands
from typing import Optional
from errorhandling.ErrorHandling import *

class ChangeStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    change = app_commands.Group(name="change", description="Change the status of the bot")

    # ----------<Change status>----------

    # Fucntion to get the desired activity
    async def get_type(self, type, name, url):
        if type == "playing":
            # Returns discord Gaming status with desired message.
            return Activity(type=discord.ActivityType.playing, name=name)
        elif type == "streaming":
            # Returns discord Streaming status with desired message and URL (if any).
            return Activity(type=discord.ActivityType.streaming, name=name, url=url)
        elif type == "listening_to":
            # Returns discord Listening status with desired message.
            return Activity(type=discord.ActivityType.listening, name=name)
        elif type == "watching":
            # Returns discord Watching status with desired message.
            return Activity(type=discord.ActivityType.watching, name=name)
        elif type == "custom":
            return discord.CustomActivity(name=name)
        else:
            # Returns nothing
            # Executes if the status has been ignored, or the user didn't select any valid option from the list.
            return None

    # Changing the status of the bot
    @change.command(name="status", description="Changing the bot status")
    @app_commands.describe(status="Status of the bot")
    @app_commands.rename(activity_type="type")
    @app_commands.describe(activity_type="The type you would like to display. Choose '(Ignore)' if you want to leave it blank.")
    @app_commands.rename(activity_name="name")
    @app_commands.describe(activity_name="The text you would like the bot to display on bio")
    @app_commands.describe(url="The URL you want to redirect (For streaming only)")
    @app_commands.choices(status=[
        app_commands.Choice(name="Idle", value="idle"),
        app_commands.Choice(name="Invisible", value="invisible"),
        app_commands.Choice(name="Do not disturb", value="dnd"),
        app_commands.Choice(name="Online", value="online")
        ])
    @app_commands.choices(activity_type=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Streaming", value="streaming"),
        app_commands.Choice(name="Listening to", value="listening_to"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Custom", value="custom"),
        app_commands.Choice(name="(Ignore)", value="ignore")
        ])
    async def change_status(self, interaction: Interaction, status: app_commands.Choice[str], activity_type: app_commands.Choice[str], activity_name: Optional[str] = None, url: Optional[str] = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message(NotBotOwnerError())
        await interaction.response.send_message("Changing status...", ephemeral=True, delete_after=0)
        # Set the status to the selected option. If none of any valid option from the list was selected, set the status to online by default.
        if status.value == "idle":
            # Set the status to idle
            status = discord.Status.idle
        elif status.value == "invisible":
            # Set the status to invisible
            status = discord.Status.invisible
        elif status.value == "dnd":
            # Set the status to dnd
            status = discord.Status.dnd
        else:
            # Set the status to online
            # Executes for online was chosen, or the user didn't select any valid option from the list.
            status = discord.Status.online
        if activity_name:
            selected_activity = await self.get_type(type=activity_type.value, name=activity_name, url=url)
        else:
            selected_activity = None
        await self.bot.change_presence(status=status, activity=selected_activity)

# ----------</Change status>----------


async def setup(bot):
    await bot.add_cog(ChangeStatus(bot))
