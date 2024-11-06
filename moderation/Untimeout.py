import discord
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.ext.commands import MissingPermissions
from typing import Optional


class Untimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Untimeout members>----------

    # Untimeouts a member
    @app_commands.command(name="untimeout", description="Remove timeouts for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to untimeout (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for untimeout")
    async def untimeout(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        untimeout_embed = Embed(title="", color=interaction.user.color)
        if reason is not None:
            await member.timeout(None, reason=reason)
            untimeout_embed.add_field(name="", value=f"{member.mention} has been **untimeout**.\nReason: **{reason}**.")
        else:
            await member.timeout(None)
            untimeout_embed.add_field(name="", value=f"{member.mention} has been **untimeout**.")
        await interaction.response.send_message(embed=untimeout_embed)

    @untimeout.error
    async def untimeout_error(self, interaction: Interaction, error):
        untimeout_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            untimeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=untimeout_error_embed)
        elif isinstance(error, BotMissingPermissions):
            untimeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **untimeout** that user. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=untimeout_error_embed)
        else:
            raise error

    # ----------</Timeout and untimeout members>----------


async def setup(bot):
    await bot.add_cog(Untimeout(bot))
