import discord
import asyncio
from discord import app_commands, Embed, Interaction, Forbidden, Permissions
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from datetime import timedelta
from typing import Optional


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Mutes a member from text channel>----------

    # Function of mutes a member from text channel
    async def mute_member(self, interaction: Interaction, member: discord.Member, days, hours, minutes, seconds, reason):
        mute_embed = Embed(title="", color=interaction.user.color)
        mute_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            muted = discord.utils.get(interaction.guild.roles, name="Muted")
            if muted is None:
                muted = await interaction.guild.create_role("Muted", permissions=Permissions(send_messages=False))
            if muted in member.roles:
                mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is already muted!")
                return await interaction.response.send_message(embed=mute_error_embed, ephemeral=True)
            else:
                if reason is not None:
                    await member.add_roles(muted, reason=reason)
                    mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds. :zipper_mouth:\nReason: **{reason}**")
                    await interaction.response.send_message(embed=mute_embed)
                else:
                    await member.add_roles(muted)
                    mute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted** for **{days}** days, **{hours}** hours, **{minutes}** minutes, and **{seconds}** seconds. :zipper_mouth:")
                    await interaction.response.send_message(embed=mute_embed)
                await asyncio.sleep(duration.total_seconds())
                await member.remove_roles(muted)
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **mute** that user. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=mute_error_embed)
            else:
                raise e

    # Mutes a member from text for a specified amount of time
    @app_commands.command(description="Mutes a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to mute")
    @app_commands.describe(reason="Reason for mute")
    async def mute(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None, days: Optional[app_commands.Range[int, 0]] = 0, hours: Optional[app_commands.Range[int, None, 23]] = 0, minutes: Optional[app_commands.Range[int, None, 59]] = 0, seconds: Optional[app_commands.Range[int, None, 59]] = 0):  # setting each value with a default value of 0 reduces a lot of the code
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
        await self.mute_member(interaction, member, days, hours, minutes, seconds, reason)

    @mute.error
    async def mute_error(self, interaction: Interaction, error):
        mute_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=mute_error_embed)
        elif isinstance(error, BotMissingPermissions):
            mute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **mute** that user. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=mute_error_embed)
        else:
            raise error
        

# ----------</Mutes a member from text channel>----------


async def setup(bot):
    await bot.add_cog(Mute(bot))
