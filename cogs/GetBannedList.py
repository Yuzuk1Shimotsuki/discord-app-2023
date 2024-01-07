import discord
from discord import SlashCommandGroup, Interaction
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from datetime import datetime


class GetBannedList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    banned = SlashCommandGroup("banned", "Action for banned people")

    # ----------<List banned members>----------

    @banned.command(name="list", description="Returns a list of banned members")
    @commands.has_permissions(ban_members=True)
    async def banned_list(self, interaction: Interaction):
        banned_list = None
        embed = discord.Embed(title=f"List of Bans in {interaction.guild}", timestamp=datetime.now(), color=discord.Colour.red())
        async for entry in interaction.guild.bans():
            if entry.user.discriminator == "0":
                # This user has no discriminator on its username
                banned_list = embed.add_field(name=f"Ban", value=f"Username: {entry.user.name}\nReason: {entry.reason}\nUser ID: {entry.user.id}\nIs Bot: {entry.user.bot}\nAccount created on: {discord.utils.format_dt(entry.user.created_at, style='R')}", inline=False)
            else:
                # This user has a custom discriminator on its username
                banned_list = embed.add_field(name=f"Ban", value=f"Username: {entry.user.name}#{entry.user.discriminator}\nReason: {entry.reason}\nUser ID: {entry.user.id}\nIs Bot: {entry.user.bot}\nAccount created on: {discord.utils.format_dt(entry.user.created_at, style='R')}", inline=False)
        if banned_list is not None:
            await interaction.response.send_message(embed=banned_list)
        else:
            await interaction.response.send_message("There are no banned members in this server so far. :slight_smile:")

    @banned_list.error
    async def banned_list_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to list banned people!")

    # ----------</List banned members>----------


def setup(bot):
    bot.add_cog(GetBannedList(bot))
