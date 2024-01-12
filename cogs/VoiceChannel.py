import discord
from discord import SlashCommandGroup, Interaction, Option, FFmpegPCMAudio
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connections = {}

    move = SlashCommandGroup("move", "Move User")

    # ----------<Voice Channels>-----------

    # Joining voice channel and start recording
    @commands.slash_command(description="Joining a voice channel")
    async def join(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to join. Leave this blank if you want the bot to join where you are.", required=False)):
        if interaction.author.voice is not None:
            if channel is not None:
                author_vc = channel
            else:
                author_vc = interaction.author.voice.channel
            voice_state = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            # This allows for more functionality with voice channels
            if voice_state == None:
                # None being the default value if the bot isnt in a channel (which is why the is_connected() is returning errors)
                # Connect the bot to voice channel
                voice = await author_vc.connect()
                await interaction.response.send_message(f"I joined the voice channel <#{author_vc.id}>")
                # #source = FFmpegPCMAudio("test.mp3")
                # #player = voice.play(source)
            elif voice.channel.id != author_vc.id:
                # The bot has been connected to a voice channel but not as same as the author or required one
                if channel is not None:
                    # The bot has been connected to a voice channel but not as same as the required one
                    await interaction.response.send_message(f'''I've already joined the voice channel :D , but not the channel you wanted me to join.
**I'm currently in:** <#{voice.channel.id}>
**The channel you wanted me to join:** <#{author_vc.id}>''')
                else:
                    # The bot has been connected to a voice channel but not as same as the author one
                    await interaction.response.send_message(f'''I've already joined the voice channel :D , but not where you are ~
**I'm currently in:** <#{voice.channel.id}>
**You're currently in:** <#{author_vc.id}>''')
            else:
                # The bot has been connected to the same channel as the author
                await interaction.response.send_message(
                    f"can u found mee in the voice channel？ i have connected to  <#{author_vc.id}> already :>")
        else:
            # The author has not joined the voice channel yet
            await interaction.response.send_message(f'''i don't want to be alone in the voice channel . . .  :pensive:
couuld u join it first before inviting meee？ :pleading_face:''')

    # Leaving voice channel
    @commands.slash_command(description="Leaving a voice channel")
    async def leave(self, interaction: Interaction):
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            # Disconnect the bot from voice channel if it has been connected
            await voice.disconnect()
            await interaction.response.send_message("I left the voice channel.")
        else:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel ^_^.")

    # Pause an audio currently playing in voice channel
    @commands.slash_command(description="Pause an audio currently playing in voice channel")
    async def pause(self, interaction: Interaction):
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        try:
            if voice.is_playing():
                voice.pause()
            else:
                await interaction.response.send_message("At the moment, there is no audio playing in the voice channel!")
        except AttributeError:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("At the moment, there is no audio playing in the voice channel or i'm not in a voice channel!")

    # Resume an paused audio in voice channel
    @commands.slash_command(description="Resume an paused audio in voice channel")
    async def resume(self, interaction: Interaction):

        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        try:
            if voice.is_paused():
                voice.resume()
            else:
                await interaction.response.send_message("At the moment, no audio was paused!")
        except AttributeError:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("At the moment, no audio was paused or i'm not in a voice channel!")

    # Stops playing audio and leave voice
    @commands.slash_command(description="Stops playing audio and leave voice")
    async def stop(self, interaction: Interaction):
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        try:
            voice.stop()
        except AttributeError:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel!")

    # Ends a voice call

    # Function to end a voice call
    async def end_voice_call(self, interaction: Interaction):
        # Disconnect the bot from voice channel if it has been connected
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            await voice.disconnect()
        # Disconnect the members from voice channel if they are connected
        for member in interaction.guild.members:
            if member.voice is not None:
                await member.move_to(None)

    # Ending a voice call
    @commands.slash_command(name="end", description="End the call for all voice channels")
    @commands.has_guild_permissions(move_members=True)
    async def end(self, interaction: Interaction):
        await self.end_voice_call(interaction)
        await interaction.response.send_message("Ended the call for all voice channels.")

    @end.error
    async def end_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to end the call!")
        else:
            raise error

    # Move all users to the voice channel which the author is already connected, or a specified voice channel.

    # Function to move all members
    async def move_all_members(self, interaction: Interaction, specified_vc, reason):
        for member in interaction.guild.members:
            if member.voice is not None:
                if reason is None:
                    await member.move_to(specified_vc)
                else:
                    await member.move_to(specified_vc, reason=reason)
        if reason is None:
            await interaction.response.send_message(f"Moved all users to <#{specified_vc.id}>.")
        else:
            await interaction.response.send_message(f"Moved all users to <#{specified_vc.id}> for **{reason}**.")

    @move.command(name="all", description="Moves all users to the specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    async def move_all(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to move user to. Leave this blank if you want to move them to where you are.", required=False), reason: Option(str, description="Reason for move", required=False)):
        if channel is None:
            specified_vc = interaction.author.voice.channel
        else:
            specified_vc = channel
        await self.move_all_members(interaction, specified_vc, reason=reason)

    @move_all.error
    async def move_all_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move all users!")
        else:
            raise error

    # Move a user to the voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="user", description="Moves a member to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    async def move_user(self, interaction: Interaction, member: Option(discord.Member, description="User to move", required=True), channel: Option(discord.VoiceChannel, description="Channel to move user to. Leave this blank if you want to move them to where you are.", required=False), reason: Option(str, description="Reason for move", required=False)):
        if channel is None:
            specified_vc = interaction.author.voice.channel
        else:
            specified_vc = channel
        if reason is None:
            await member.move_to(specified_vc)
            await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> by <@{interaction.author.id}>.")
        else:
            await member.move_to(specified_vc, reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> by <@{interaction.author.id}> for **{reason}**")

    @move_user.error
    async def move_user_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move users!")
        else:
            raise error

    # Moves the author to another specified voice channel
    @move.command(name="me", description="Moves you to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    async def move_me(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to move you to.", required=True), reason: Option(str, description="Reason for move", required=False)):
        if reason is None:
            await interaction.author.move_to(channel)
            await interaction.response.send_message(f"<@{interaction.author.id}> has been moved to <#{channel.id}>.")
        else:
            await interaction.author.move_to(channel, reason=reason)
            await interaction.response.send_message(f"<@{interaction.author.id}> has been moved to <#{channel.id}> for {reason}")

    @move_me.error
    async def move_me_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move yourself!")
        else:
            raise error
        
    # Moves the bot to another specified voice channel
    @move.command(name="bot", description="Moves me to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(moderate_members=True)
    async def move_bot(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to move me to.", required=True), reason: Option(str, description="Reason for move", required=False)):
        if reason is None:
            await interaction.author.move_to(channel)
            await interaction.response.send_message(f"I moved to <#{channel.id}>.")
        else:
            await interaction.author.move_to(channel, reason=reason)
            await interaction.response.send_message(f"I moved to <#{channel.id}> for {reason}")

    @move_bot.error
    async def move_bot_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move me!")
        else:
            raise error

    # ----------</Voice Channels>----------


def setup(bot):
    bot.add_cog(VoiceChannel(bot))
