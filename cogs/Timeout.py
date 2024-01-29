import discord
from discord import Interaction, Option
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from datetime import timedelta


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
            await member.timeout_for(duration)
            await interaction.response.send_message(f"<@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds by <@{interaction.author.id}>.")
        else:
            await member.timeout_for(duration, reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds by <@{interaction.author.id}> for '{reason}'.")

    # Timeouts a member for a specified amount of time
    @commands.slash_command(name="timeout", description="Timeouts a member")
    @commands.has_guild_permissions(moderate_members=True)
    async def timeout(self, interaction: Interaction, member: Option(discord.Member, required=True), reason: Option(str, required=False), days: Option(int, min_value=0, max_value=27, default=0, required=False), hours: Option(int, min_value=0, max_value=23, default=0, required=False), minutes: Option(int, min_value=0, max_value=59, default=0, required=False), seconds: Option(int, min_value=0, max_value=59, default=0, required=False)):  # setting each value with a default value of 0 reduces a lot of the code
        if member.id == interaction.author.id:
            await interaction.response.send_message("BRUH! You can't timeout yourself!")
            return
        elif member.id == self.bot.application_id:
            # To prevent the bot bans itself from the server by accident
            await interaction.response.send_message(f"i cannot just timeout myself ^u^")
        elif member.guild_permissions.administrator:
            if interaction.author.id == interaction.guild.owner.id:
                await self.timeout_member(interaction, member, days, hours, minutes, seconds, reason)
            else:
                await interaction.response.send_message("You can't do this, this person is a moderator!")
                return
        else:
            await self.timeout_member(interaction, member, days, hours, minutes, seconds, reason)

    @timeout.error
    async def timeouterror(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

# ----------</Timeouts a member>----------


def setup(bot):
    bot.add_cog(Timeout(bot))
  