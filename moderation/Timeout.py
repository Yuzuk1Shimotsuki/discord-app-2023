import discord
import asyncio
from discord import app_commands, Embed, Interaction, Forbidden
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from datetime import timedelta
from typing import Optional


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Timeouts a member>----------

    # Function of timeout a member
    async def timeout_member(self, interaction: Interaction, member, days, hours, minutes, seconds, reason):
        timeout_embed = Embed(title="", color=interaction.user.color)
        timeout_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            duration = timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
            if duration >= timedelta(days = 28):    # Check if the total time exceeds 28 days
                timeout_error_embed.add_field(name="", value=f"I can't **timeout** someone for **more than 28 days**!")
                return await interaction.response.send_message(embed=timeout_error_embed, ephemeral = True)
            if reason is not None:
                await member.timeout(duration, reason=reason)
                timeout_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **timeout** for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds. :zipper_mouth:\nReason: **{reason}**")
            else:
                await member.timeout(duration)
                timeout_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **timeout** for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds. :zipper_mouth:")
            await interaction.response.send_message(embed=timeout_embed)
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **timeout** that user. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=timeout_error_embed)

    # Timeouts a member for a specified amount of time
    @app_commands.command(description="Timeouts a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to timeout")
    @app_commands.describe(reason="Reason for timeout")
    async def timeout(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None, days: Optional[app_commands.Range[int, 0]] = 0, hours: Optional[app_commands.Range[int, None, 23]] = 0, minutes: Optional[app_commands.Range[int, None, 59]] = 0, seconds: Optional[app_commands.Range[int, None, 59]] = 0):  # setting each value with a default value of 0 reduces a lot of the code
        timeout_error_embed = Embed(title="", color=discord.Colour.red())
        if member == interaction.user:
            timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, You can't **timeout yourself**!")
            return await interaction.response.send_message(embed=timeout_error_embed)
        if member.guild_permissions.administrator and interaction.user != interaction.guild.owner:
            if not await self.bot.is_owner(interaction.user):
                timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Stop trying to **timeout an admin**! :rolling_eyes:")
                return await interaction.response.send_message(embed=timeout_error_embed)
        if member == self.bot.user:
            timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **timeout myself**!")
            return await interaction.response.send_message(embed=timeout_error_embed)
        await self.timeout_member(interaction, member, days, hours, minutes, seconds, reason)

    @timeout.error
    async def timeout_error(self, interaction: Interaction, error):
        timeout_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=timeout_error_embed)
        elif isinstance(error, BotMissingPermissions):
            timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **timeout** that user. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=timeout_error_embed)
        else:
            raise error

# ----------</Timeouts a member>----------


async def setup(bot):
    await bot.add_cog(Timeout(bot))
