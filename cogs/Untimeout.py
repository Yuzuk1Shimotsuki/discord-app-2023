import discord
from discord import Interaction, Option
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class Untimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Untimeout members>----------

    # Untimeouts a member
    @commands.slash_command(name="untimeout", description="Remove timeouts for a member")
    @commands.has_guild_permissions(moderate_members=True)
    async def untimeout(self, interaction: Interaction, member: Option(discord.Member, required=True), reason: Option(str, required=False)):
        if reason == None:
            await member.remove_timeout()
            await interaction.response.send_message(f"<@{member.id}> has been untimed out by <@{ctx.author.id}>.")
        else:
            await member.remove_timeout(reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been untimed out by <@{ctx.author.id}>. Reason: {reason}.")

    @untimeout.error
    async def untimeout_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # ----------</Timeout and untimeout members>----------


def setup(bot):
    bot.add_cog(Untimeout(bot))
