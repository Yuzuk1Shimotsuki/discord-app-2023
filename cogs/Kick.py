import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from typing import Optional


class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # ----------<Kick members>----------

    # Kicks a member from the entire server
    @app_commands.command(description="Kicks a member")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(member="User to kick")
    @app_commands.rename(member="user")
    @app_commands.describe(reason="Reason for kick")
    async def kick(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        # Executes if the user currently in the server
        try:
            if member.id == interaction.user.id:
                # Checks to see if they're the same
                await interaction.response.send_message("BRUH! You can't kick yourself!")
            elif member.id == self.bot.application_id:
                # To prevent the bot kicks itself away the server by accident
                await interaction.response.send_message(f"i cannot just kick myself away the server ^u^")
            elif member.guild_permissions.administrator:
                # Only server owner has privilege to kick an admin. Admins are not alowed to kick another admins
                if interaction.user.id == interaction.guild.owner.id:
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
    @app_commands.command(description="Kicks a member from the voice channel")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.describe(member="User to kick")
    @app_commands.rename(member="user")
    @app_commands.describe(reason="Reason for kick")
    async def vkick(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        try:
            if member.id == interaction.user.id:
                # Checks to see if they're the same
                await interaction.response.send_message("BRUH! You can't kick yourself!")
            elif member.id == self.bot.application_id:
                # To prevent the bot kicks itself away the server by accident
                await interaction.response.send_message(f"i cannot just kick myself away the voice ^u^")
            elif member.guild_permissions.administrator:
                # Only server owner has privilege to kick an admin. Admins are not alowed to kick another admins
                if interaction.user.id == interaction.guild.owner.id:
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


async def setup(bot):
    await bot.add_cog(Kick(bot))
