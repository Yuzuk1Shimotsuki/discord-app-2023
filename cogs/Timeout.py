import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from datetime import timedelta
from typing import Optional


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Timeouts a member>----------

    # Function of timeout a member
    async def timeout_member(self, interaction: Interaction, member, days, hours, minutes, seconds, reason):
        duration = timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
        if duration >= timedelta(days = 28): #added to check if time exceeds 28 days
            await interaction.response.send_message("I can't timeout someone for more than 28 days!", ephemeral = True) #responds, but only the author can see the response
            return
        if reason == None:
            await member.timeout(duration)
            await interaction.response.send_message(f"<@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds by <@{interaction.user.id}>.")
        else:
            await member.timeout(duration, reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds by <@{interaction.user.id}> for '{reason}'.")

    # Timeouts a member for a specified amount of time
    @app_commands.command(name="timeout", description="Timeouts a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to timeout")
    @app_commands.describe(reason="Reason for timeout")
    async def timeout(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None, days: Optional[app_commands.Range[int, 0]] = 0, hours: Optional[app_commands.Range[int, None, 23]] = 0, minutes: Optional[app_commands.Range[int, None, 59]] = 0, seconds: Optional[app_commands.Range[int, None, 59]] = 0):  # setting each value with a default value of 0 reduces a lot of the code
        if member.id == interaction.user.id:
            return await interaction.response.send_message("BRUH! You can't timeout yourself!")
        elif member.id == self.bot.application_id:
            # To prevent the bot bans itself from the server by accident
            await interaction.response.send_message(f"i cannot just timeout myself ^u^")
        elif member.guild_permissions.administrator:
            if interaction.user.id == interaction.guild.owner.id:
                await self.timeout_member(interaction, member, days, hours, minutes, seconds, reason)
            else:
                return await interaction.response.send_message("You can't do this, this person is a moderator!")
        else:
            await self.timeout_member(interaction, member, days, hours, minutes, seconds, reason)

    @timeout.error
    async def timeouterror(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

# ----------</Timeouts a member>----------


async def setup(bot):
    await bot.add_cog(Timeout(bot))
