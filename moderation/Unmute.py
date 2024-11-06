import discord
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.ext.commands import MissingPermissions
from typing import Optional


class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Unmutes a member from text channel>----------

    # Unmutes a member from text
    @app_commands.command(description="Unmutes a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unmute (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for unmute")
    async def unmute(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        unmute_embed = Embed(title="", color=interaction.user.color)
        unmute_error_embed = Embed(title="", color=discord.Colour.red())
        muted = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted not in member.roles:
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not muted** currently.")
            return await interaction.response.send_message(embed=unmute_error_embed)
        if reason is None:
            await member.remove_roles(muted)
            unmute_embed.add_field(name="", value=f"{member.mention} has been **unmuted**.")
        else:
            await member.remove_roles(muted, reason=reason)
            unmute_embed.add_field(name="", value=f"{member.mention} has been **unmuted**.\nReason: **{reason}**.")
        await interaction.response.send_message(embed=unmute_embed)

    @unmute.error
    async def unmute_error(self, interaction: Interaction, error):
        unmute_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=unmute_error_embed)
        elif isinstance(error, BotMissingPermissions):
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **unmute** that user. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=unmute_error_embed)
        else:
            raise error

    # ----------</Unmutes a member from text channel>----------


async def setup(bot):
    await bot.add_cog(Unmute(bot))
