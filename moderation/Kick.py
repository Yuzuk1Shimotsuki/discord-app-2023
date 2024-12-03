import discord
from discord import app_commands, Embed, Interaction, Forbidden
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from typing import Optional


class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    # ----------<Kick members>----------


    # Kicks a member from the entire server
    @app_commands.command(description="Kicks a member")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.checks.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="User to kick")
    @app_commands.rename(member="user")
    @app_commands.describe(reason="Reason for kick")
    async def kick(self, interaction: Interaction, member: discord.User, reason: Optional[str] = None):
        kick_embed = Embed(title="", color=interaction.user.color)
        kick_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            
            if interaction.guild.get_member(member.id) is None:
                kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not in the server** currently.")
                return await interaction.response.send_message(embed=kick_error_embed)
            
            if member == interaction.user:
                kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, You can't **kick yourself**!")
                return await interaction.response.send_message(embed=kick_error_embed)
            
            if member == self.bot.user:
                kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **kick myself**!")
                return await interaction.response.send_message(embed=kick_error_embed)
            
            if member.guild_permissions.administrator and interaction.user != interaction.guild.owner:
                
                if not await self.bot.is_owner(interaction.user):
                    kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Stop trying to **ban an admin**! :rolling_eyes:")
                    return await interaction.response.send_message(embed=kick_error_embed)
            
            if reason is not None:
                await member.kick(reason=reason)
                kick_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **kicked**.\nReason: **{reason}**")
            
            else:
                await member.kick()
                kick_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **kicked**.")        
            
            return await interaction.response.send_message(embed=kick_embed)
        
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **kick** that user. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=kick_error_embed)
            
            else:
                raise e


    @kick.error
    async def kick_error(self, interaction: Interaction, error):
        kick_error_embed = Embed(title="", color=discord.Colour.red())
        
        if isinstance(error, MissingPermissions):
            kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `kick_members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=kick_error_embed)
        
        elif isinstance(error, BotMissingPermissions):
            kick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **kick** that member. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=kick_error_embed)
        
        else:
            raise error


# ----------</Kick members>----------


async def setup(bot):
    await bot.add_cog(Kick(bot))
