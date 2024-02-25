import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from typing import Optional


class Untimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Untimeout members>----------

    # Untimeouts a member
    @app_commands.command(name="untimeout", description="Remove timeouts for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to untimeout (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for untimeout")
    async def untimeout(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        if reason == None:
            await member.timeout(None)
            await interaction.response.send_message(f"<@{member.id}> has been untimed out by <@{interaction.user.id}>.")
        else:
            await member.timeout(None, reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been untimed out by <@{interaction.user.id}>. Reason: {reason}.")

    @untimeout.error
    async def untimeout_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # ----------</Timeout and untimeout members>----------


async def setup(bot):
    await bot.add_cog(Untimeout(bot))
