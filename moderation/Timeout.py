import discord
import re
from discord import app_commands, Embed, Interaction, Forbidden
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from datetime import timedelta
from typing import Optional, Union


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # ----------<Timeouts a member>----------


    # Convert time string to seconds and detailed duration breakdown (< 28 days / 4 weeks)
    def parse_duration(self, duration_str: str) -> Union[dict, str]:
        units = {
            "s": 1,        # seconds
            "m": 60,       # minutes
            "h": 3600,     # hours
            "d": 86400,    # days
            "w": 604800,   # weeks
        }

        matches = re.findall(r"(\d+)(mo|[smhdwy])", duration_str)
        
        if not matches:
            return "error_improper_format"

        total_seconds = 0
        duration_breakdown = {
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
                    "w": "weeks",
                    "d": "days",
                    "h": "hours",
                    "m": "minutes",
                    "s": "seconds"
                }[unit]] += int(amount)

        
        duration_breakdown["total_seconds"] = total_seconds
        return duration_breakdown


    # Function of timeout a member
    async def timeout_member(self, interaction: Interaction, member: discord.Member, duration_str: str, reason: str):
        timeout_embed = Embed(title="", color=interaction.user.color)
        timeout_error_embed = Embed(title="", color=discord.Colour.red())
        
        try:
            total_duration = self.parse_duration(duration_str)
            
            if total_duration == "error_improper_format":
                timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like the time fomrmat you entered it's not vaild :thinking:... Perhaps enter again and gave me a chance to handle it, {interaction.user.mention} :pleading_face:?", inline=False)
                timeout_error_embed.add_field(name="Supported time format:", value=f"**1**s = **1** second | **2**m = **2** minutes | **5**h = **5** hours | **10**d = **10** days | **3**w = **3** weeks. Must be less than **28** days in total.", inline=False)
                return await interaction.response.send_message(embed=timeout_error_embed)
            
            if total_duration["total_seconds"] >= 2419200:   # Check if the total time exceeds 28 days / 2419200 seconds
                timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **timeout** someone for **more than 28 days**!")
                return await interaction.response.send_message(embed=timeout_error_embed, ephemeral = True)
            
            duration_message = "for " + " and ".join(", ".join([f"**{value}** {unit[:-1]}" + ("s" if value > 1 else "") for unit, value in total_duration.items() if unit != "total_seconds" and value != 0]).rsplit(", ", 1)) + " " if duration_str is not None else ""
            reason_message =  f"\nReason: **{reason}**" if reason is not None else ""
            
            if reason is not None:
                await member.timeout(timedelta(seconds=total_duration["total_seconds"]), reason=reason)
            
            else:
                await member.timeout(timedelta(seconds=total_duration["total_seconds"]))
            
            timeout_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **timeout** {duration_message}:zipper_mouth:{reason_message}")
            await interaction.response.send_message(embed=timeout_embed)
        
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                timeout_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **timeout** that user. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=timeout_error_embed)


    # Timeouts a member for a specified amount of time
    @app_commands.command(description="Timeouts a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to timeout")
    @app_commands.describe(reason="Reason for timeout")
    @app_commands.describe(duration="Duration for timeout (e.g. 1s = 1 second | 2m = 2 minutes | 5h = 5 hours | 10d = 10 days | 3w = 3 weeks). Must be less than 28 days in total.")
    async def timeout(self, interaction: Interaction, member: discord.Member, duration: str, reason: Optional[str] = None):
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
        
        await self.timeout_member(interaction, member, duration, reason)


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
