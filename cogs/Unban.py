import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from typing import Optional


class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Unban users>----------

    # Unban users
    @app_commands.command(description="Unbans a member")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user="User to remove the ban of (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for unban")
    async def unban(self, interaction: Interaction, user: discord.User, reason: Optional[str] = None):
        try:
            await interaction.guild.unban(user)
            if reason is None:
                await interaction.response.send_message(f"{user.mention} has been **unbanned**.")
            else:
                await interaction.response.send_message(f"{user.mention} has been **unbanned**. Reason: **{reason}**")
        except discord.errors.NotFound:
            await interaction.response.send_message(f"{user.mention} is **not banned** currently.")

    # Handle errors while unbanning a user
    @unban.error
    async def unban_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you **don't have permission** to **unban users**!")
        else:
            raise error

    # ----------</Unban users>----------


async def setup(bot):
    await bot.add_cog(Unban(bot))
