import discord
from discord import app_commands, Embed, Interaction, Forbidden
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from typing import Optional


class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Unban users>----------

    # Banned list lookup
    async def is_banned(self, interaction: Interaction, user: discord.User) -> bool:
        is_banned = False
        async for entry in interaction.guild.bans():
            if entry.user.id == user.id:
                is_banned = True
                break
        return is_banned

    # Unban users
    @app_commands.command(description="Unbans a member")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user="User to remove the ban of (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for unban")
    async def unban(self, interaction: Interaction, user: discord.User, reason: Optional[str] = None):
        unban_embed = Embed(title="", color=interaction.user.color)
        unban_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            if not await self.is_banned(interaction, user):
                unban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {user.mention} is **not banned** currently.")
                return await interaction.response.send_message(embed=unban_error_embed)
            if reason is None:
                await interaction.guild.unban(user)
                unban_embed.add_field(name="", value=f":white_check_mark: {user.mention} has been **unbanned**.")
            else:
                await interaction.guild.unban(user, reason=reason)
                unban_embed.add_field(name="", value=f":white_check_mark: {user.mention} has been **unbanned**.\nReason: **{reason}**")
            await interaction.response.send_message(embed=unban_embed)
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                unban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **unban** that user. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=unban_error_embed)
            else:
                raise e

    # Handle errors while unbanning a user
    @unban.error
    async def unban_error(self, interaction: Interaction, error):
        unban_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            unban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `ban_members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=unban_error_embed)
        else:
            raise error

    # ----------</Unban users>----------


async def setup(bot):
    await bot.add_cog(Unban(bot))
