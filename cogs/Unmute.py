import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from typing import Optional


class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    unmute = app_commands.Group(name="unmute", description="Unmute people")

    # ----------<Unmutes a member from text or voice channel>----------

    # Unmutes a member from text
    @unmute.command(name="text", description="Unmutes a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unmute (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for unmute")
    async def unmute_text(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        muted = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted not in member.roles:
            await interaction.response.send_message(f"<@{member.id}> has not been muted!", ephemeral=True)
            return
        else:
            if reason is None:
                await member.remove_roles(muted)
                await interaction.response.send_message(f"<@{member.id}> has been unmuted from text by <@{interaction.user.id}>.")
            else:
                await member.remove_roles(muted, reason=reason)
                await interaction.response.send_message(f"<@{member.id}> has been unmuted from text by <@{interaction.user.id}>. Reason: {reason}.")

    @unmute_text.error
    async def unmute_text_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # Unmutes a member from voice
    @unmute.command(name="voice", description="Unmutes a member from voice channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unmute (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for unmute")
    async def unmute_voice(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        if reason is None:
            await member.edit(mute=False)
            await interaction.response.send_message(f"<@{member.id}> has been unmuted from voice by <@{interaction.user.id}>.")
        else:
            await member.edit(mute=False, reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been unmuted from voice by <@{interaction.user.id}>. Reason: {reason}.")

    @unmute_voice.error
    async def unmute_voice_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # ----------</Unmutes a member from text or voice channel>----------


async def setup(bot):
    await bot.add_cog(Unmute(bot))
