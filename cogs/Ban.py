import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from typing import Optional


class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ban = app_commands.Group(name="ban", description="Bans an user")

    # ----------<Ban users or members>----------

    # Function for banning a user or member
    async def bans_user(self, interaction: Interaction, user, reason, ban_from_guild):
        if not ban_from_guild:
            await user.ban(reason=reason)
        else:
            await interaction.guild.ban(user, reason=reason)
        await interaction.response.send_message(f"<@{user.id}> has been **banned**. Reason: **{reason}**")

    # Check if the user is already banned or not
    async def banned_list_lookup(self, interaction, user):
        is_banned = False
        async for entry in interaction.guild.bans():
            if entry.user.id == user.id:
                is_banned = True
                break
        return is_banned

    # Function to check if the author is able to ban the user or not
    async def ban_check(self, interaction, user, reason, ban_from_guild):
        if user.id == interaction.user.id:
            # checks to see if they're the same
            await interaction.response.send_message("BRUH! You can't **ban yourself**!")
        elif user.id == self.bot.application_id:
            # To prevent the bot bans itself from the server by accident
            await interaction.response.send_message(f"i cannot just **ban myself** from the server ^u^")
        # Checks to see if the user is banned from the server
        elif await self.banned_list_lookup(interaction, user):
            await interaction.response.send_message(f"<@{user.id}> has been **already banned**!")
        # Checks to see if ban from guild or ban members is used
        elif ban_from_guild:
            await self.bans_user(interaction, user, reason, ban_from_guild=True)
        # Executes the following if the user currently in the server
        elif interaction.guild.get_member(user.id) is not None:
            if user.guild_permissions.administrator:
                # Only server owner has privilege to ban an admin. Admins are not alowed to ban another admins
                if interaction.user.id == interaction.guild.owner.id:
                    # The author is the server owner
                    await self.bans_user(interaction=interaction, user=user, reason=reason, ban_from_guild=False)
                else:
                    # The author is not the server owner
                    await interaction.response.send_message("Stop trying to **ban an admin**! :rolling_eyes:")
            else:
                await self.bans_user(interaction=interaction, user=user, reason=reason, ban_from_guild=False)
        else:
            await interaction.response.send_message(f"<@{user.id}> is **not in the server** currently.\nTo **ban them from the server**, use the command </ban guild:1187832408888840205> instead. :wink:")

    # Ban users who is in the guild or not with user_id
    @ban.command(name="guild", description="Bans a user or member with the corresponding user_id")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(user="User to ban (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for ban")
    async def ban_guild(self, interaction: Interaction, user: discord.User, reason: Optional[str] = None):
        await self.ban_check(interaction=interaction, user=user, reason=reason, ban_from_guild=True)

    # Ban members in the server
    @ban.command(name="member", description="Bans a member")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(member="Member to ban")
    @app_commands.describe(reason="Reason for ban")
    async def ban_member(self, interaction: Interaction, member: discord.User, reason: Optional[str] = None):
        await self.ban_check(interaction=interaction, user=member, reason=reason, ban_from_guild=False)

    @ban_member.error
    async def on_ban_member_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you **don't have permission** to **ban members**!")
        else:
            raise error

    @ban_guild.error
    async def on_ban_guild_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you **don't have permission** to **ban users**!")
        else:
            raise error

# ----------</Ban users or members>----------


async def setup(bot):
    await bot.add_cog(Ban(bot))
