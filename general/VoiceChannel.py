import discord
import wavelink
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from typing import cast, Optional
from general.VoiceChannelFallbackConfig import *
from errorhandling.ErrorHandling import *

recording_vc = {}
    
# Main cog, heavily rewrited after wavelink implementation
class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        # General init
        global set_fallback_channel
        global recording_vc
        self.bot = bot

    move = app_commands.Group(name="move", description="Move User")

    # ----------<Voice Channels>-----------

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        global recording_vc
        # Ensure:
        # - this is a channel leave as opposed to anything else
        # Actions:
        # - Reset all settings if the bot leave or being kicked by someone else

        if member != self.bot.user:
            return

        if (
            after.channel is None and  # if this is None this is certainly a leave
            before.channel != after.channel  # if these match then this could be e.g. server deafen
        ):
            guild_id = before.channel.guild.id
            # Send fallback and reset all settings
            if guild_id in fallback_text_channel:
                left_vc = discord.Embed(title="", description="", color=self.bot.user.color)
                left_vc.add_field(name="", value="I left the voice channel.")
                await fallback_text_channel[guild_id].send(embed=left_vc, silent=True)
                del fallback_text_channel[guild_id]
            # Reset the music player
            reset_music_player(guild_id)
            recording_vc[guild_id] = None

    # General commands

    # Joining voice channel
    @app_commands.command(description="Invokes me to a voice channel")
    @app_commands.describe(channel="Channel to join. Leave this blank if you want the bot to join where you are.")
    async def join(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        join_embed = discord.Embed(title="", color=interaction.user.colour)
        if interaction.user.voice is not None:
            voice_channel = channel or interaction.user.voice.channel
        if voice_channel is None:
            # The author is not in a voice channel, or not specified which voice channel the application should join
            return await interaction.followup.send(embed=AuthorNotInVoiceError(interaction, interaction.user).return_embed())
        if not player:
            try:
                # Join voice channel
                player = await voice_channel.connect(cls=wavelink.Player)
                set_fallback_text_channel(interaction, interaction.channel)
                join_embed.add_field(name="", value=f"I've joined the voice channel {voice_channel.mention}")
                return await interaction.response.send_message(embed=join_embed)
            except discord.ClientException:
                # Something went wrong on discord or network side while joining voice channel
                join_embed.add_field(name="", value=f"I was unable to join {interaction.user.voice.channel}. Please try again.", inline=False)
                return await interaction.response.send_message(embed=join_embed)
        elif player.channel != voice_channel:
            # The bot has been connected to a voice channel but not as same as the author or required one
            if channel is not None:
                # The bot has been connected to a voice channel but not as same as the required one
                await interaction.response.send_message(embed=BotAlreadyInVoiceError(interaction, player.channel, voice_channel).notrequired())
            else:
                # The bot has been connected to a voice channel but not as same as the author one
                await interaction.response.send_message(embed=BotAlreadyInVoiceError(interaction, player.channel, voice_channel).notauthor())
        else:
            # The bot has been connected to the same channel as the author
            await interaction.response.send_message(embed=BotAlreadyInVoiceError(interaction, player.channel, voice_channel).same())

    # Leaving voice channel
    @app_commands.command(description="Leaving a voice channel")
    async def leave(self, interaction: Interaction):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        if player is not None:
            # Disconnect the bot from voice channel if it has been connected
            await player.disconnect()
            await interaction.response.send_message("Leaving...", ephemeral=True, delete_after=0)
        else:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel ^_^.")

    # Moving all users or ends a voice call

    # Function to move all members (Can move them to any voice channel in the server, or use None to kick them away from the vc)
    async def move_all_members(self, interaction: Interaction, specified_vc, reason):
        moved_count = 0
        for member in interaction.guild.members:
            if member.voice is not None:
                if reason is None:
                    await member.move_to(specified_vc)
                else:
                    await member.move_to(specified_vc, reason=reason)
                moved_count += 1
        if moved_count == 0:
            return False
        return True
    
    # Ending a voice call
    @app_commands.command(name="end", description="End the call for all voice channels")
    @app_commands.checks.has_permissions(move_members=True)
    async def end(self, interaction: Interaction):
        await interaction.response.send_message("Ending the call for all voice channels...")
        if await self.move_all_members(interaction, None, None):
            await interaction.edit_original_response(content="Ended the call for all voice channels.")

    @end.error
    async def end_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to end the call!")
        else:
            raise error
    
    # Move all users to the voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="all", description="Moves all users to the specified voice channel")
    @app_commands.checks.has_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move them to. Leave this blank if you want to move them into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_all(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move all connected members into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move them all into right now, {interaction.user.mention}?''')
        else:
            specified_vc = channel
        await interaction.response.send_message(f"Moving all users to {specified_vc.mention}...")
        # Return True when successful to move, or return False when no users were found in the voice channel.
        if await self.move_all_members(interaction, specified_vc, reason=reason):
            if reason is None:
                await interaction.edit_original_response(content=f"All users has been moved to {specified_vc.mention}.")
            else:
                await interaction.edit_original_response(content=f"All users has been moved to {specified_vc.mention} for **{reason}**.")
        else:
            # No users were found in the voice channel
            await interaction.edit_original_response(content=f"No users were found in the voice channel.")


    @move_all.error
    async def move_all_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move all users!")
        else:
            raise error

    # Move an user to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="user", description="Moves a member to another specified voice channel")
    @app_commands.describe(member="Member to move")
    @app_commands.describe(channel="Channel to move user to. Leave this blank if you want to move the user into where you are.")
    @app_commands.describe(reason="Reason for move")
    @commands.has_guild_permissions(move_members=True)
    async def move_user(self, interaction: Interaction, member: discord.Member, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        # Check the target user was in the vc or not
        if member.voice is None and interaction.user.id == self.bot.application_id:
            return await interaction.response.send_message(f"I'm currently not in a voice channel.")
        elif interaction.user.voice is None:
            return await interaction.response.send_message(f"You're currently not in a voice channel !")
        elif member.voice is None:
            return await interaction.response.send_message(f"{member.mention} currently not in a voice channel.")
        # Check the target vc
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move someone into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move {member.mention} into right now, {interaction.user.mention}?''')
        else:
            specified_vc = channel
        if reason is None:
            await member.move_to(specified_vc)
            if interaction.user.id == self.bot.application_id:
                return await interaction.response.send_message(f"I have been moved to {specified_vc.mention}. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.")
            await interaction.response.send_message(f"{member.mention} has been moved to {specified_vc.mention}.")
        else:
            await member.move_to(specified_vc, reason=reason)
            if interaction.user.id == self.bot.application_id:
                return await interaction.response.send_message(f"I have been moved to {specified_vc.mention} for **{reason}**. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.")
            await interaction.response.send_message(f"{member.mention} has been moved to {specified_vc.mention} for **{reason}**")

    @move_user.error
    async def move_user_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move users!")
        else:
            raise error

    # Moves the author to another specified voice channel
    @move.command(name="me", description="Moves you to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move you to.")
    @app_commands.describe(reason="Reason for move")
    async def move_me(self, interaction: Interaction, channel: discord.VoiceChannel, reason: Optional[str] = None):
        # Check the target user was in the vc or not
        if interaction.user.voice is None:
            return await interaction.response.send_message(f"You're currently not in a voice channel!")
        if reason is None:
            await interaction.user.move_to(channel)
            await interaction.response.send_message(f"{interaction.user.mention} has been moved to <#{channel.id}>.")
        else:
            await interaction.user.move_to(channel, reason=reason)
            await interaction.response.send_message(f"{interaction.user.mention} has been moved to <#{channel.id}> for {reason}")

    @move_me.error
    async def move_me_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move yourself!")
        else:
            raise error
        
    # Moves the bot to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="bot", description="Moves me to another specified voice channel")
    @app_commands.checks.has_permissions(move_members=True, moderate_members=True)
    @app_commands.describe(channel="Channel to move me to. Leave this blank if you want to move me into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_bot(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        # Check the bot was in the vc or not
        if player is None:
            return await interaction.response.send_message(f"I'm currently not in a voice channel.")
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move me into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move into right now, {interaction.user.mention}?''')
        else:
            specified_vc = channel
        if reason is None:
            await player.move_to(specified_vc)
            await interaction.response.send_message(f"I have been moved to {specified_vc.mention}.")
        else:
            await player.move_to(specified_vc, reason=reason)
            await interaction.response.send_message(f"I have been moved to {specified_vc.mention} for **{reason}**.")

    @move_bot.error
    async def move_bot_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move me!")
        else:
            raise error

    # discord.py has no recording vc function.

    """
        
    # Recording voice channels

    # Start recording callback function
    async def finished_callback(self, sink, interaction: Interaction):
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        if recorded_users == []:
            return await interaction.followup.send(f"Nobody were talking in the voice channel, so no audio recorded.")
        try:
            files = [
                discord.File(audio.file, f"{user_id}.{sink.encoding}")
                for user_id, audio in sink.audio_data.items()
            ]
            await interaction.followup.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files)
        except discord.errors.HTTPException as file_error:
            if file_error.status == 413:
                await interaction.followup.send(f"An error occured while saving the recorded audio: 413 Payload Too Large (error code: 40005): Request entity too large")
            else:
                raise file_error

    # Start the recording of voice channels
    @commands.slash_command(description="Start the recording of voice channels")
    async def start(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.author.voice is not None:
            guild_id = interaction.guild.id
            self.recording_vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if self.recording_vc[guild_id] is None:
                self.recording_vc[guild_id] = await interaction.author.voice.channel.connect()
            try:    
                self.recording_vc[guild_id].start_recording(
                discord.sinks.OGGSink(),  # The sink type to use.
                self.finished_callback,  # What to do once done.
                interaction)
                await interaction.followup.send("Recording voice channels...")
            except discord.sinks.errors.RecordingException:
                await interaction.followup.send("There's a recording already going on right now.")
        else:
            await interaction.followup.send(AuthorNotInVoiceError(interaction, interaction.author))

    # Stop the recording of a voice channel
    @commands.slash_command(description="Stop the recording of a voice channel")
    async def finish(self, interaction: Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild.id
        if guild_id in self.recording_vc:
            await interaction.followup.send(f"Saving audio...", delete_after=0)
            self.recording_vc[guild_id].stop_recording()
            del self.recording_vc[guild_id]
        else:
            await interaction.followup.send("I wasn't recording audio in this guild.")

    """

    # ----------</Voice Channels>----------


async def setup(bot):
    await bot.add_cog(VoiceChannel(bot))
