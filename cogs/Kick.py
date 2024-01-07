import discord
from discord import SlashCommandGroup, Interaction, Option
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    voice = SlashCommandGroup("voice", "Voice Channel Commands")

    # ----------<Kick members>----------

    # Kicks a member from the entire server
    @commands.slash_command(description="Kicks a member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, interaction: Interaction, member: Option(discord.Member, name="user", description="User to kick", required=True), reason: Option(str, description="Reason for kick", required=False)):
        # Executes if the user currently in the server
        try:
            if member.id == interaction.author.id:
                # Checks to see if they're the same
                await interaction.response.send_message("BRUH! You can't kick yourself!")
            elif member.id == self.bot.application_id:
                # To prevent the bot kicks itself away the server by accident
                await interaction.response.send_message(f"i cannot just kick myself away the server ^u^")
            elif member.guild_permissions.administrator:
                # Only server owner has privilege to kick an admin. Admins are not alowed to kick another admins
                if interaction.author.id == interaction.guild.owner.id:
                    # The author is the server owner
                    await member.kick(reason=reason)
                    await interaction.response.send_message(f"<@{member.id}> **has been kicked**. **Reason:** {reason}")
                else:
                    # The author is not the server owner
                    await interaction.response.send_message("Stop trying to kick an admin! :rolling_eyes:")
            else:
                await member.kick(reason=reason)
                await interaction.response.send_message(f"<@{member.id}> **has been kicked**. **Reason:** {reason}")
        except AttributeError:
            # The user is not in the server currently
            await interaction.response.send_message(f"<@{member.id}> is not in the server currently.")

    @kick.error
    async def kick_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to kick users!")
        else:
            raise error

    # Kicks a member from voice
    @commands.slash_command(description="Kicks a member from the voice channel")
    async def vkick(self, interaction: Interaction, member: Option(discord.Member, required=True), reason: Option(str, required=False)):
        try:
            if member.id == interaction.author.id:
                # Checks to see if they're the same
                await interaction.response.send_message("BRUH! You can't kick yourself!")
            elif member.id == self.bot.application_id:
                # To prevent the bot kicks itself away the server by accident
                await interaction.response.send_message(f"i cannot just kick myself away the voice ^u^")
            elif member.guild_permissions.administrator:
                # Only server owner has privilege to kick an admin. Admins are not alowed to kick another admins
                if interaction.author.id == interaction.guild.owner.id:
                    # The author is the server owner
                    await member.move_to(None)
                    await interaction.response.send_message(f"<@{member.id}> **has been kicked from voice**. **Reason:** {reason}")
                else:
                    # The author is not the server owner
                    await interaction.response.send_message("Stop trying to kick an admin! :rolling_eyes:")
            else:
                await member.move_to(None)
                await interaction.response.send_message(f"<@{member.id}> **has been kicked from voice**. **Reason:** {reason}")
        except AttributeError:
            # The user is not in the voice currently
            await interaction.response.send_message(f"<@{member.id}> is not in the voice currently.")

# ----------</Kick members>----------


def setup(bot):
    bot.add_cog(Kick(bot))
