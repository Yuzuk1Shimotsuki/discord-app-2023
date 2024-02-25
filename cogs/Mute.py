import discord
import asyncio
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from datetime import timedelta
from typing import Optional


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    mute = app_commands.Group(name="mute", description="Mute people")

    # ----------<Mutes a member from text or voice channel>----------

    # Function of mutes a member from text channel
    async def mute_member_text(self, interaction: Interaction, member, days, hours, minutes, seconds, reason):
        duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        muted = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted in member.roles:
            await interaction.response.send_message(f"<@{member.id}> is already muted!", ephemeral=True)
            return
        else:
            if reason == None:
                await member.add_roles(muted)
                await interaction.response.send_message(f":white_check_mark: <@{member.id}> muted from the text for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds by <@{interaction.user.id}>! :zipper_mouth:")
            else:
                await member.add_roles(muted, reason=reason)
                await interaction.response.send_message(f":white_check_mark: <@{member.id}> muted from the text for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds by <@{interaction.user.id}>! :zipper_mouth: **Reason: {reason}**")
            await asyncio.sleep(duration.total_seconds())
            await member.remove_roles(muted)

    # Mutes a member from text for a specified amount of time
    @mute.command(name="text", description="Mutes a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to mute")
    async def mute_text(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None, days: Optional[app_commands.Range[int, 0]] = 0, hours: Optional[app_commands.Range[int, None, 23]] = 0, minutes: Optional[app_commands.Range[int, None, 59]] = 0, seconds: Optional[app_commands.Range[int, None, 59]] = 0):  # setting each value with a default value of 0 reduces a lot of the code
        if member.id == interaction.user.id:
            await interaction.response.send_message("BRUH! You can't mute yourself!")
            return
        elif member.id == self.bot.application_id:
            # To prevent the bot bans itself from the server by accident
            await interaction.response.send_message(f"i cannot just mute myself ^u^")
        elif member.guild_permissions.administrator:
            if interaction.user.id == interaction.guild.owner.id:
                await self.mute_member_text(interaction, member, days, hours, minutes, seconds, reason)
            else:
                await interaction.response.send_message("You can't do this, this person is a moderator!")
                return
        else:
            await self.mute_member_text(interaction, member, days, hours, minutes, seconds, reason)

    @mute_text.error
    async def mute_text_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # Function of mutes a member from voice channel
    async def mute_member_voice(self, interaction: Interaction, member, days, hours, minutes, seconds, reason):
        duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        muted = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted in member.roles:
            await interaction.response.send_message(f"<@!{member.id}> is already muted!", ephemeral=True)
            return
        else:
            if reason == None:
                await member.edit(mute=True)
                await interaction.response.send_message(f":white_check_mark: <@{member.id}> muted from voice for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds by <@{interaction.user.id}>! :zipper_mouth:")
            else:
                await member.edit(mute=True, reason=reason)
                await interaction.response.send_message(f":white_check_mark: <@{member.id}> muted from voice for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds by <@{interaction.user.id}>! :zipper_mouth: **Reason: {reason}**")
            await asyncio.sleep(duration.total_seconds())
            await member.edit(mute=False)

    # Mutes a member from voice for a specified amount of time
    @mute.command(name="voice", description="Mutes a member from voice channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to mute")
    async def mute_voice(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None, days: Optional[app_commands.Range[int, 0]] = 0, hours: Optional[app_commands.Range[int, None, 23]] = 0, minutes: Optional[app_commands.Range[int, None, 59]] = 0, seconds: Optional[app_commands.Range[int, None, 59]] = 0):  # setting each value with a default value of 0 reduces a lot of the code
        if member.id == interaction.user.id:
            await interaction.response.send_message("BRUH! You can't mute yourself!")
            return
        elif member.id == self.bot.application_id:
            # To prevent the bot bans itself from the server by accident
            await interaction.response.send_message(f"i cannot just mute myself ^u^")
        elif member.guild_permissions.administrator:
            if interaction.user.id == interaction.guild.owner.id:
                await self.mute_member_text(interaction, member, days, hours, minutes, seconds, reason)
            else:
                await interaction.response.send_message("You can't do this, this person is a moderator!")
                return
        else:
            await self.mute_member_voice(interaction, member, days, hours, minutes, seconds, reason)

    @mute_voice.error
    async def mute_voice_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

# ----------</Mutes a member from text or voice channel>----------


async def setup(bot):
    await bot.add_cog(Mute(bot))
