import discord
import asyncio
import re
from discord import app_commands, Embed, Interaction, Forbidden, Permissions
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from typing import Optional, Union


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Mutes a member from text channel>----------

    # Convert time string to seconds and detailed duration breakdown
    def parse_duration(self, duration_str: str) -> Union[dict, str]:
        units = {
            "s": 1,        # seconds
            "m": 60,       # minutes
            "h": 3600,     # hours
            "d": 86400,    # days
            "w": 604800,   # weeks
            "mo": 2592000, # months (approximate)
            "y": 31536000  # years (approximate)
        }

        matches = re.findall(r"(\d+)(mo|[smhdwy])", duration_str)
        if not matches:
            return "error_improper_format"

        total_seconds = 0
        duration_breakdown = {
            "years": 0,
            "months": 0,
            "weeks": 0,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0
        }

        for amount, unit in matches:
            if unit in units:
                total_seconds += int(amount) * units[unit]
                duration_breakdown[{
                    "y": "years",
                    "mo": "months",
                    "w": "weeks",
                    "d": "days",
                    "h": "hours",
                    "m": "minutes",
                    "s": "seconds"
                }[unit]] += int(amount)

        duration_breakdown["total_seconds"] = total_seconds
        return duration_breakdown

    # Function of mutes a member from text channel
    async def mute_text(self, interaction: Interaction, member: discord.Member, duration_str: str | None, reason: str | None):
        mute_embed = Embed(title="", color=interaction.user.color)
        mute_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            muted = discord.utils.get(interaction.guild.roles, name="Muted")
            if duration_str is not None:  # For time-based mute only
                total_duration = self.parse_duration(duration_str)
                if total_duration == "error_improper_format":
                    mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like the time fomrmat you entered it's not vaild :thinking: ... Perhaps enter again and gave me a chance to handle it, {interaction.user.mention} :pleading_face:?", inline=False)
                    mute_error_embed.add_field(name="Supported time format:", value=f"**1**s = **1** second | **2**m = **2** minutes | **5**h = **5** hours | **10**d = **10** days | **3**w = **3** weeks | **6**y = **6** years.", inline=False)
                    return await interaction.response.send_message(embed=mute_error_embed)
            if muted is None:
                muted = await interaction.guild.create_role("Muted", permissions=Permissions(send_messages=False))
            if muted in member.roles:
                mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is already muted!")
                return await interaction.response.send_message(embed=mute_error_embed, ephemeral=True)
            duration_message = "for " + " and ".join(", ".join([f"**{value}** {unit[:-1]}" + ("s" if value > 1 else "") for unit, value in total_duration.items() if unit != "total_seconds" and value != 0]).rsplit(", ", 1)) + " " if duration_str is not None else ""
            reason_message =  f"\nReason: **{reason}**" if reason is not None else ""
            if reason is not None:
                await member.add_roles(muted, reason=reason)
            else:
                await member.add_roles(muted)
            mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** {duration_message}:zipper_mouth:{reason_message}")
            await interaction.response.send_message(embed=mute_embed)
            if duration_str is not None:  # For time-based mute only
                await asyncio.sleep(total_duration["total_seconds"])
                if muted in member.roles:
                    await member.remove_roles(muted, reason=f"Automatically unmuted after {duration_str}.")
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
