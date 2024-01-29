import discord
from discord import SlashCommandGroup, Interaction, Option, Activity, Game, Streaming
from discord.ext import commands

# Default options from discord
options = ["Idle", "Invisible", "Do not disturb", "Online"]
types = ["Playing", "Streaming", "Listening to", "Watching", "(Ignore)"]


class ChangeStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global options
        global types

    change = SlashCommandGroup("change", "Change the status of the bot")

    # ----------<Change status>----------

    # Fucntion to get the desired activity
    async def get_type(self, type, name, url):
        name = name or "?help"
        if type == types[0]:
            # Returns discord Gaming status with desired message.
            return Game(name=name)
        elif type == types[1]:
            # Returns discord Streaming status with desired message and URL (if any).
            return Streaming(name=name, url=url)
        elif type == types[2]:
            # Returns discord Listening status with desired message.
            return Activity(type=discord.ActivityType.listening, name=name)
        elif type == types[3]:
            # Returns discord Watching status with desired message.
            return Activity(type=discord.ActivityType.watching, name=name)
        else:
            # Returns nothing
            # Executes if the status has been ignored, or the user didn't select any valid option from the list.
            return None

    # Changing the status of the bot
    @change.command(name="status", description="Changing the bot status")
    async def status(self, interation: Interaction, status: Option(str, choices=options, description="Status of the bot", required=True), activity_type: Option(str, name="type", choices=types, description="The type u would like to display. Choose '(Ignore)' if u want to leave it blank.", required=True), activity_name: Option(str, name="name", description="The message u would like to display", required=False), url: Option(str, description="The URL u want to redirect (For streaming only)", required=False)):
        await interation.response.send_message("Changing status...", ephemeral=True, delete_after=0)
        # Set the status to the selected option. If none of any valid option from the list was selected, set the status to online by default.
        if status == options[0]:
            # Set the status to idle
            status = discord.Status.idle
        elif status == options[1]:
            # Set the status to invisible
            status = discord.Status.invisible
        elif status == options[2]:
            # Set the status to dnd
            status = discord.Status.dnd
        else:
            # Set the status to online
            # Executes for online was chosen, or the user didn't select any valid option from the list.
            status = discord.Status.online
        selected_activity = await self.get_type(type=activity_type, name=activity_name, url=url)
        await self.bot.change_presence(status=status, activity=selected_activity)

# ----------</Change status>----------


def setup(bot):
    bot.add_cog(ChangeStatus(bot))
