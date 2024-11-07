import discord
import asyncio
import re
from discord import app_commands, Embed, Interaction, Forbidden, Permissions
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from typing import Optional


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Mutes a member from text channel>----------

    # Getting total seconds from timestring
    def timestring_converter(self, timestr):
        time_matches = re.findall(r"(\d+)(mo|[smhdwy])", timestr)
        if time_matches == []:
            return "error_improper_format"
        time_units = {
                    "s": 1,        # seconds
                    "m": 60,       # minutes
                    "h": 3600,     # hours
                    "d": 86400,    # days
                    "w": 604800,   # weeks
                    "mo": 2592000, # months (approximation)
                    "y": 31536000  # years (approximation)
                }
        # Calculate the total duration in seconds
        total_seconds = 0
        seconds = 0
        minutes = 0
        hours = 0
        days = 0
        weeks = 0
        months = 0
        years = 0
        for amount, unit in time_matches:
            if unit == "":
                return "error_improper_format"
            if unit == "s":
                seconds += int(amount)
            if unit == "m":
                minutes += int(amount)
            if unit == "h":
                hours += int(amount)
            if unit == "d":
                days += int(amount)
            if unit == "w":
                weeks += int(amount)
            if unit == "mo":
                months += int(amount)
            if unit == "y":
                years += int(amount)
            if unit in time_units:
                total_seconds += int(amount) * time_units[unit]
        return {"years": years, "months": months, "weeks": weeks, "days": days, "hours": hours, "minutes": minutes, "seconds": seconds, "total_seconds": total_seconds}

    # Function of mutes a member from text channel
    async def mute_text(self, interaction: Interaction, member: discord.Member, timestring: str | None, reason: str):
        mute_embed = Embed(title="", color=interaction.user.color)
        mute_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            muted = discord.utils.get(interaction.guild.roles, name="Muted")
            if timestring is not None:  # For time-based mute only
                total_duration = self.timestring_converter(timestring)
                if total_duration == "error_improper_format":
                    mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like the time fomrmat you entered it's not vaild :thinking: ... Perhaps enter again and gave me a chance to handle it, {interaction.user.mention} :pleading_face:?", inline=False)
                    mute_error_embed.add_field(name="Supported time format:", value=f"**1**s = **1** second | **2**m = **2** minutes | **5**h = **5** hours | **10**d = **10** days | **3**w = **3** weeks | **6**y = **6** years.", inline=False)
                    return await interaction.response.send_message(embed=mute_error_embed)
            if muted is None:
                muted = await interaction.guild.create_role("Muted", permissions=Permissions(send_messages=False))
            if muted in member.roles:
                mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is already muted!")
                return await interaction.response.send_message(embed=mute_error_embed, ephemeral=True)
            if reason is not None:
                await member.add_roles(muted, reason=reason)
                if timestring is None:
                    # Infinity
                    mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** :zipper_mouth:\nReason: **{reason}**")
                else:
                    # Time-based
                    mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** for {'**' + str(total_duration["years"]) + '**' if total_duration["years"] != 0 else ''}{' year(s), ' if total_duration["years"] != 0 else ''}{'**' + str(total_duration["months"]) + '**' if total_duration["months"] != 0 else ''}{' month(s), ' if total_duration["months"] != 0 else ''}{'**' + str(total_duration["weeks"]) + '**' if total_duration["weeks"] != 0 else ''}{' week(s), ' if total_duration["weeks"] != 0 else ''}{'**' + str(total_duration["days"]) + '**' if total_duration["days"] != 0 else ''}{' day(s), ' if total_duration["days"] != 0 else ''}{'**' + str(total_duration["hours"]) + '**' if total_duration["hours"] != 0 else ''}{' hour(s), ' if total_duration["hours"] != 0 else ''}{'**' + str(total_duration["minutes"]) + '**' if total_duration["minutes"] != 0 else ''}{' minute(s), ' if total_duration["minutes"] != 0 else ''}{'**' + str(total_duration["seconds"]) + '**' if total_duration["seconds"] != 0 else ''}{' second(s). ' if total_duration["seconds"] != 0 else ''}:zipper_mouth:\nReason: **{reason}**")
            else:
                await member.add_roles(muted)
                if timestring is None:
                    # Infinity
                    mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** :zipper_mouth:")
                else:
                    # Time-based
                    mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** for {'**' + str(total_duration["years"]) + '**' if total_duration["years"] != 0 else ''}{' year(s), ' if total_duration["years"] != 0 else ''}{'**' + str(total_duration["months"]) + '**' if total_duration["months"] != 0 else ''}{' month(s), ' if total_duration["months"] != 0 else ''}{'**' + str(total_duration["weeks"]) + '**' if total_duration["weeks"] != 0 else ''}{' week(s), ' if total_duration["weeks"] != 0 else ''}{'**' + str(total_duration["days"]) + '**' if total_duration["days"] != 0 else ''}{' day(s), ' if total_duration["days"] != 0 else ''}{'**' + str(total_duration["hours"]) + '**' if total_duration["hours"] != 0 else ''}{' hour(s), ' if total_duration["hours"] != 0 else ''}{'**' + str(total_duration["minutes"]) + '**' if total_duration["minutes"] != 0 else ''}{' minute(s), ' if total_duration["minutes"] != 0 else ''}{'**' + str(total_duration["seconds"]) + '**' if total_duration["seconds"] != 0 else ''}{' second(s). ' if total_duration["seconds"] != 0 else ''}:zipper_mouth:")
            await interaction.response.send_message(embed=mute_embed)
            if timestring is not None:  # For time-based mute only
                await asyncio.sleep(total_duration["total_seconds"])
                if muted in member.roles:
                    await member.remove_roles(muted, reason=f"Automatically unmuted after {timestring}.")
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **mute** that user by changing the user's roles. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=mute_error_embed)
            else:
                raise e

    # Mutes a member from text for a specified amount of time
    @app_commands.command(description="Mutes a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to mute")
    @app_commands.describe(reason="Reason for mute")
    @app_commands.describe(duration="Duration for mute (e.g. 1s = 1 second | 2m = 2 minutes | 5h = 5 hours | 10d = 10 days | 3w = 3 weeks | 6y = 6 years)")
    async def mute(self, interaction: Interaction, member: discord.Member, duration: Optional[str] = None, reason: Optional[str] = None):
        mute_error_embed = Embed(title="", color=discord.Colour.red())
        if member == interaction.user:
            mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, You can't **mute yourself**!")
            return await interaction.response.send_message(embed=mute_error_embed)
        if member.guild_permissions.administrator and interaction.user != interaction.guild.owner:
            if not await self.bot.is_owner(interaction.user):
                mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Stop trying to **mute an admin**! :rolling_eyes:")
                return await interaction.response.send_message(embed=mute_error_embed)
        if member == self.bot.user:
            mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **mute myself**!")
            return await interaction.response.send_message(embed=mute_error_embed)
        await self.mute_text(interaction, member, duration, reason)

    @mute.error
    async def mute_error(self, interaction: Interaction, error):
        mute_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=mute_error_embed)
        elif isinstance(error, BotMissingPermissions):
            mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **mute** that user by changing the user's roles. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=mute_error_embed)
        else:
            raise error
        

# ----------</Mutes a member from text channel>----------


async def setup(bot):
    await bot.add_cog(Mute(bot))
