import discord
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from datetime import datetime


class GetBannedList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    banned = app_commands.Group(name="banned", description="Action for banned people")


    # ----------<List banned members>----------


    @banned.command(name="list", description="Returns a list of banned members")
    @app_commands.checks.has_permissions(ban_members=True)
    async def banned_list(self, interaction: Interaction):
        banned_list = None
        banned_list_embed = Embed(title=f"List of Bans in {interaction.guild}", timestamp=datetime.now(), color=discord.Colour.red())
        
        async for entry in interaction.guild.bans():
            
            if entry.user.discriminator == "0":
                # This user has no discriminator on its username
                banned_list = banned_list_embed.add_field(name=f"Ban", value=f"Username: {entry.user.name}\nReason: {entry.reason}\nUser ID: {entry.user.id}\nIs Bot: {entry.user.bot}\nAccount created on: {discord.utils.format_dt(entry.user.created_at, style='R')}", inline=False)
            
            else:
                # This user has a custom discriminator on its username
                banned_list = banned_list_embed.add_field(name=f"Ban", value=f"Username: {entry.user.name}#{entry.user.discriminator}\nReason: {entry.reason}\nUser ID: {entry.user.id}\nIs Bot: {entry.user.bot}\nAccount created on: {discord.utils.format_dt(entry.user.created_at, style='R')}", inline=False)
        
        if banned_list is not None:
            await interaction.response.send_message(banned_list_embed=banned_list)
        
        else:
            await interaction.response.send_message("There are no banned members in this server so far. :slight_smile:")


    @banned_list.error
    async def banned_list_error(self, interaction: Interaction, error):
        banned_list_error_embed = Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            banned_list_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `ban members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=banned_list_error_embed)
        
        elif isinstance(error, BotMissingPermissions):
            banned_list_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **list all banned users**. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=banned_list_error_embed)


    # ----------</List banned members>----------


async def setup(bot):
    await bot.add_cog(GetBannedList(bot))
