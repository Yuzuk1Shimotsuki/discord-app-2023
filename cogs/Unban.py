import discord
from discord import Interaction, Option
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Unban members>----------

    # Unban members
    @commands.slash_command(description="Unbans a member")
    @commands.has_permissions(ban_members=True)
    async def unban(self, interaction: Interaction, user: Option(discord.Member, description="User to remove the ban of (Enter the User ID e.g. 529872483195806124)", required=True), reason: Option(str, description="Reason for unban", required=False)):
        try:
            await interaction.guild.unban(user)
            if reason is None:
                await interaction.response.send_message(f"{user.mention} has been unbanned.")
            else:
                await interaction.response.send_message(f"{user.mention} has been unbanned. Reason: {reason}")
        except discord.errors.NotFound:
            await interaction.response.send_message(f"{user.mention} is not banned currently.")

    # Handle errors while unbanning a user
    @unban.error
    async def unban_error(self, interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to unban users!")
        else:
            await interaction.response.send_message(
                f"Something went wrong, I couldn't unban this user or this user isn't banned.")
            raise error

    # ----------</Unban members>----------


def setup(bot):
    bot.add_cog(Unban(bot))
