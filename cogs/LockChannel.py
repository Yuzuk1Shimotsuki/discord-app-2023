import discord
from discord import SlashCommandGroup, Interaction, Option, PermissionOverwrite
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class LockChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    antiraid = SlashCommandGroup("antiraid", "Commands to lock all channels")

    # ----------<Locks and unlocks text channels>----------

    # Function for locking a text channel
    async def lock_channels(self, interaction, channel, reason):
        roles = interaction.guild.roles
        overwrite = PermissionOverwrite()
        overwrite.send_messages = False
        overwrite.create_public_threads = False
        overwrite.create_private_threads = False
        overwrite.send_messages_in_threads = False
        try:
            await channel.set_permissions(roles[0], overwrite=overwrite, reason=reason)
            return True
        except Exception as e:
            return False

    # Function for unlocking a text channel
    async def unlock_channels(self, interaction, channel, reason):
        roles = interaction.guild.roles
        try:
            await channel.set_permissions(roles[0], overwrite=None, reason=reason)
            return True
        except Exception as e:
            return False

    # Function for checking a text channel is locked or not
    async def is_locked(self, channel, interaction):
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        checklist = ["send_messages", "create_public_threads", "create_private_threads", "send_messages_in_threads"]
        check_count = 0
        for check_item in checklist:
            if overwrite.__getattribute__(check_item) is False:
                check_count += 1
        if check_count == 4:
            return True
        elif check_count == 0:
            return False
        else:
            return "partialy_true"

    # Locks all text channels
    @antiraid.command(name="activate", description="Locks all text channels for everyone")
    @commands.has_permissions(administrator=True)
    @commands.has_permissions(manage_channels=True)
    @commands.has_permissions(manage_guild=True)
    async def antiraid_activate(self, interaction: Interaction, reason: Option(str, description="Reason for anti-raid", required=False)):
        await interaction.response.defer()
        channels = interaction.guild.text_channels
        is_locked_channels_count = 0
        successful_locked_channels_count = 0
        for channel in channels:
            if await self.is_locked(channel, interaction) is True:
                is_locked_channels_count += 1
            elif await self.is_locked(channel, interaction) is False:
                if await self.lock_channels(interaction, channel, reason) is True:
                    successful_locked_channels_count += 1
        if is_locked_channels_count == len(channels):
            await interaction.followup.send(f"Anti-raid mode is already activated!")
        elif successful_locked_channels_count == len(channels):
            await interaction.followup.send(f"Anti-raid mode has been activated. Reason: {reason}")
        else:
            await interaction.followup.send(f"Looks like anti-raid mode was activated improperly :thinking:...")

    @antiraid_activate.error
    async def antiraid_activate_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permissions to activate anti-raid mode!")
        else:
            raise error

    # Unlocks all text channels
    @antiraid.command(name="deactivate", description="Unlocks all text channels for everyone")
    @commands.has_permissions(administrator=True)
    @commands.has_permissions(manage_channels=True)
    @commands.has_permissions(manage_guild=True)
    async def antiraid_deactivate(self, interaction: Interaction, reason: Option(str, description="Reason for deactivating anti-raid", required=False)):
        await interaction.response.defer()
        channels = interaction.guild.text_channels
        is_unlocked_channels_count = 0
        successful_unlocked_channels_count = 0
        for channel in channels:
            if await self.is_locked(channel, interaction) is True:
                if await self.unlock_channels(interaction, channel, reason) is True:
                    successful_unlocked_channels_count += 1
            elif await self.is_locked(channel, interaction) is False:
                is_unlocked_channels_count += 1
        if successful_unlocked_channels_count == len(channels):
            await interaction.followup.send(f"Anti-raid mode has been deactivated. Reason: {reason}")
        elif is_unlocked_channels_count == len(channels):
            await interaction.followup.send(f"Anti-raid mode is not activated!")
        else:
            await interaction.followup.send(f"Looks like anti-raid mode was deactivated improperly :thinking:...")

    @antiraid_deactivate.error
    async def antiraid_deactivate_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message(
                "It seems that you don't have permissions to deactivate anti-raid mode!")
        else:
            raise error

    # Locks the current or a specified text channel
    @commands.slash_command(name="lock", description="Locks the current or a specified text channel for everyone")
    @commands.has_permissions(administrator=True)
    @commands.has_permissions(manage_channels=True)
    async def lock(self, interaction: Interaction, channel: Option(discord.TextChannel, description="Text channel to lock. Leave this blank if you want to lock the current text channel.", required=False), reason: Option(str, description="Reason for lock", required=False)):
        await interaction.response.defer()
        channel = channel or interaction.channel
        if await self.is_locked(channel, interaction) is True:
            await interaction.followup.send(f"Channel <#{channel.id}> is already locked!")
        elif await self.is_locked(channel, interaction) is False:
            if await self.lock_channels(interaction, channel, reason) is True:
                await interaction.followup.send(f"Channel <#{channel.id}> has been locked. Reason: {reason}")
        else:
            await interaction.followup.send(f"Looks like channel <#{channel.id}> is locked improperly :thinking:...")

    @lock.error
    async def lock_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permissions to lock a channel!")
        else:
            raise error

    # Unlocks the current or a specified channel
    @commands.slash_command(name="unlock", description="Unlocks the current or a specified text channel for everyone")
    @commands.has_permissions(administrator=True)
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, interaction: Interaction, channel: Option(discord.TextChannel, description="Text channel to unlock. Leave this blank if you want to unlock the current text channel.", required=False), reason: Option(str, description="Reason for unlock", required=False)):
        await interaction.response.defer()
        channel = channel or interaction.channel
        if await self.is_locked(channel, interaction) is True:
            if await self.unlock_channels(interaction, channel, reason) is True:
                await interaction.followup.send(f"Channel <#{channel.id}> has been unlocked. Reason: {reason}")
        elif await self.is_locked(channel, interaction) is False:
            await interaction.followup.send(f"Channel <#{channel.id}> is already unlocked!")
        else:
            await interaction.followup.send(
                f"Looks like channel <#{channel.id}> is locked improperly :thinking:... u need to lock it in a proper way before unlock it!")

    @unlock.error
    async def unlock_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permissions to unlock a channel!")
        else:
            raise error

# ----------</Locks and unlocks text channels>----------


def setup(bot):
    bot.add_cog(LockChannel(bot))
