import discord
from discord import app_commands, Embed, Interaction, Forbidden
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from typing import Optional

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ban = app_commands.Group(name="ban", description="Bans a user")

    # ----------<Ban users or members>----------

    # Main session to ban a user
    async def ban_user(self, interaction: Interaction, user: discord.User, reason: Optional[str], ban_from_guild: bool):
        ban_embed = Embed(title="", color=interaction.user.color)
        ban_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            # Ban action for guild or member
            if ban_from_guild:
                if reason is not None:
                    await interaction.guild.ban(user, reason=reason)
                    ban_embed.add_field(name="", value=f":white_check_mark: {user.mention} has been **banned from guild**.\nReason: **{reason}**")
                else:
                    await interaction.guild.ban(user)
                    ban_embed.add_field(name="", value=f":white_check_mark: {user.mention} has been **banned from guild**.")
            # Permission check: Only server owner (or bot owner) has privileges to ban admins
            elif user.guild_permissions.administrator and interaction.user != interaction.guild.owner:
                if not await self.bot.is_owner(interaction.user):
                    ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Stop trying to **ban an admin**! :rolling_eyes:")
                    return await interaction.response.send_message(embed=ban_error_embed)
            else:
                if reason is not None:
                    await user.ban(reason=reason)
                    ban_embed.add_field(name="", value=f":white_check_mark: {user.mention} has been **banned**.\nReason: **{reason}**")
                else:
                    await user.ban()
                    ban_embed.add_field(name="", value=f":white_check_mark: {user.mention} has been **banned**.")
            await interaction.response.send_message(embed=ban_embed)
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **ban** that user. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=ban_error_embed)
            else:
                raise e


    # Check for conditions
    async def check_ban_conditions(self, interaction: Interaction, user: discord.User, reason: Optional[str], ban_from_guild: bool):
        ban_error_embed = Embed(title="", color=discord.Colour.red())
        if interaction.guild.get_member(user.id) is None and not ban_from_guild:
            ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {user.mention} is **not in the server** currently.\nTo **ban them from the server**, use the command </ban guild:1187832408888840205> instead. :wink:")
            return await interaction.response.send_message(embed=ban_error_embed)
        if user == interaction.user:
            ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, You can't **ban yourself**!")
            return await interaction.response.send_message(embed=ban_error_embed)
        if user == self.bot.user:
            ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **ban myself**!")
            return await interaction.response.send_message(embed=ban_error_embed)
        if await self.is_banned(interaction, user):
            ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {user.mention} is **already banned**!")
            return await interaction.response.send_message(embed=ban_error_embed)
        await self.ban_user(interaction, user, reason, ban_from_guild)

    # Banned list lookup
    async def is_banned(self, interaction: Interaction, user: discord.User) -> bool:
        is_banned = False
        async for entry in interaction.guild.bans():
            if entry.user.id == user.id:
                is_banned = True
                break
        return is_banned

    # Ban users in the guild or by using user_id
    @ban.command(name="guild", description="Ban a user by their user ID from the guild")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="User to ban (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for ban")
    async def ban_guild(self, interaction: Interaction, user: discord.User, reason: Optional[str] = None):
        await self.check_ban_conditions(interaction, user, reason, ban_from_guild=True)

    # Ban members in the server
    @ban.command(name="member", description="Bans a member currently in the server")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.bot_has_permissions(ban_members=True)
    @app_commands.describe(member="Member to ban")
    @app_commands.describe(reason="Reason for ban")
    async def ban_member(self, interaction: Interaction, member: discord.User, reason: Optional[str] = None):
        await self.check_ban_conditions(interaction, member, reason, ban_from_guild=False)

    # Error handling
    @ban_guild.error
    @ban_member.error
    async def ban_error(self, interaction: Interaction, error):
        ban_error_embed = Embed(title="", color=discord.Colour.red())
        if isinstance(error, MissingPermissions):
            ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `ban_members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=ban_error_embed)
        elif isinstance(error, BotMissingPermissions):
            ban_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **ban** that user. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=ban_error_embed)
        else:
            raise error

# ----------</Ban users or members>----------

async def setup(bot):
    await bot.add_cog(Ban(bot))
