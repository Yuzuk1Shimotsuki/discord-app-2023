import discord
import asyncio
from discord import SlashCommandGroup, Interaction, Option, FFmpegPCMAudio
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from ast import alias
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL


class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        # General init
        self.bot = bot
        # Music playing from YT
        # all the music related stuff
        self.is_playing = {}
        self.is_paused = {}
        self.current_music_queue_index = {}
        self.music_queue = {}
        self.YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
        self.FFMPEG_OPTIONS = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

        self.vc = {}
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)
        # Recording VC
        self.rec_vc = {}
        self.is_recording = {}


    move = SlashCommandGroup("move", "Move User")

    # ----------<Voice Channels>-----------

    # Startup
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            guild_id = int(guild.id)
            # 2d array containing [song, channel]
            self.music_queue[guild_id] = []
            self.current_music_queue_index[guild_id] = 0
            self.vc[guild_id] = None
            self.is_paused[guild_id] = self.is_playing[guild_id] = False
            self.rec_vc[guild_id] = None
            self.is_recording[guild_id] = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member != self.bot.user:
            return
        vc = member.guild.voice_client
        guild_id = before.channel.guild.id
        # Ensure:
        # - this is a channel move as opposed to anything else
        # - this is our instance's voice client and we can action upon it
        if (
            before.channel and  # if this is None this could be a join
            after.channel and  # if this is None this could be a leave
            before.channel != after.channel and  # if these match then this could be e.g. server deafen
            isinstance(vc, discord.VoiceClient) and  # None & not external Protocol check
            vc.channel == after.channel  # our current voice client is in this channel
        ):
            # If the voice was intentionally paused don't resume it for no reason
            if vc.is_paused():
                return
            # If the voice isn't playing anything there is no sense in trying to resume
            if not vc.is_playing():
                return     
            await asyncio.sleep(0.5)  # wait a moment for it to set in
            vc.pause()
            vc.resume()

        # Reset all settings if the bot leave or being kicked by someone else
        if (
            before.channel and  # if this is None this could be a join
            after.channel is None and  # if this is None this could be a leave
            before.channel != after.channel and  # if these match then this could be e.g. server deafen
            isinstance(vc, discord.VoiceClient) and  # None & not external Protocol check
            vc == None  # our current voice client is in this channel
        ):
            # Reset all settings on guild
            self.music_queue[guild_id] = []
            self.current_music_queue_index[guild_id] = 0
            self.vc[guild_id] = None
            self.is_paused[guild_id] = self.is_playing[guild_id] = False
            self.rec_vc[guild_id] = None
            self.is_recording[guild_id] = False

    # Searching the item on YouTube
    def search_yt(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=False)["title"]
            return {'source':item, 'title':title}
        search = VideosSearch(item, limit=10)
        return {'source':search.result()["result"][0]["link"], 'title':search.result()["result"][0]["title"]}

    # Infinite loop checking 
    async def auto_play_next(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if self.current_music_queue_index[guild_id] < len(self.music_queue[guild_id]):
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            self.current_music_queue_index[guild_id] += 1
            m_url = self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['source']
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
            song = data['url']
            self.vc[guild_id].play(discord.FFmpegPCMAudio(song, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.auto_play_next(interaction), self.bot.loop))
        else:
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False

    # Plays Music
    async def play_music(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if self.current_music_queue_index[guild_id] < len(self.music_queue[guild_id]):
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            m_url = self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['source']
            # Try to connect to voice channel if the bot is not already connected
            if self.vc[guild_id] is None:
                self.vc[guild_id] = await interaction.author.voice.channel.connect()
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
            song = data['url']
            self.vc[guild_id].play(discord.FFmpegPCMAudio(song, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.auto_play_next(interaction), self.bot.loop))
        else:
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False

    # Auto search from YouTube
    async def get_youtube_search_result(self: discord.AutocompleteContext):
        source = self.options['source']
        query = self.options["query"]
        if query is None:
            query = ""
        if source == 'YouTube':
            result_list = []
            if not query.startswith("https://"):
                try:
                    max_limit = 25
                    search = VideosSearch(query, limit=max_limit)
                    for i in range(max_limit):
                        try:
                            result_list.append(search.result()["result"][i]["title"])
                        except IndexError:
                            break
                    return result_list
                except TypeError:
                    # The author did not entered anything yet
                    # Originally it should return a defult list on Windows, not sure why it's not working on linux...
                    return []
            return []
        else:
            # The source is not from YouTube
            return []

    # Play selected tracks from YouTube
    @commands.slash_command(description="Play selected tracks from YouTube")
    async def play(self, interaction:Interaction, source: discord.Option(str, choices=['YouTube']), query: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_youtube_search_result), description="Link or keywords of the track you want to play.")):
        guild_id = interaction.guild.id
        play_embed = discord.Embed(title="", color=interaction.author.colour)
        try:
            voice_channel = interaction.author.voice.channel
        except:
            play_embed.add_field(name="", value="Connect to a voice channel first.", inline=False)
            await interaction.response.send_message(embed=play_embed)
            return
        if self.is_paused[guild_id]:
            self.vc[guild_id].resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                play_embed.add_field(name="", value="Could not download the song: Incorrect format. Try another keywords. This could be due to the link you entered is a playlist or livestream format.", inline=False)
                await interaction.response.send_message(embed=play_embed)
            else:
                if self.is_playing[guild_id]:
                    play_embed.add_field(name="", value=f"**#{len(self.music_queue[guild_id])+1} - '{song['title']}'** added to the queue", inline=False)
                else:
                    play_embed.add_field(name="", value=f"**'{song['title']}'** added to the queue", inline=False)
                self.music_queue[guild_id].append([song, voice_channel])
                await interaction.response.send_message(embed=play_embed)
                if self.is_playing[guild_id] == False:
                    self.current_music_queue_index[guild_id] = 0
                    await self.play_music(interaction)
                    
    # Pauses the current song being played in voice channel
    @commands.slash_command(name="pause", help="Pauses the current song being played in voice channel")
    async def pause(self, interaction: Interaction):
        guild_id = interaction.guild.id
        pause_embed = discord.Embed(title="", color=interaction.author.colour)
        if self.is_playing[guild_id]:
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = True
            self.vc[guild_id].pause()
            pause_embed.add_field(name="", value="The track has been paused.", inline=False)
        elif self.is_paused[guild_id]:
            pause_embed.add_field(name="", value="The track has been already paused.", inline=False)
        await interaction.response.send_message(embed=pause_embed)

    # Resume a paused track in voice channel
    @commands.slash_command(name = "resume", description="Resume a paused track in voice channel")
    async def resume(self, interaction: Interaction):
        guild_id = interaction.guild.id
        resume_embed = discord.Embed(title="", color=interaction.author.colour)
        if self.is_paused[guild_id]:
            self.is_paused[guild_id] = False
            self.is_playing[guild_id] = True
            self.vc[guild_id].resume()
            resume_embed.add_field(name="", value="Resuming the track...", inline=False)
            await interaction.response.send_message(embed=resume_embed)
            
    # Skips the current track being played in voice channel
    @commands.slash_command(name="skip", description="Skips the current track being played in voice channel")
    async def skip(self, interaction: Interaction, amount: Option(int, min = 1, description="Number of track to skip. Leave this blank if you want to skip the current track only.", required=False)):
        guild_id = interaction.guild.id
        skip_embed = discord.Embed(title="", color=interaction.author.colour)
        if self.vc[guild_id] != None and self.vc[guild_id]:
            # Skip mutiple tracks
            if amount is not None and amount < len(self.music_queue[guild_id]) - (self.current_music_queue_index[guild_id]):
                self.current_music_queue_index[guild_id] += amount - 1
                skip_embed.add_field(name="", value=f"Skipped **{amount}** tracks in the queue", inline=False)
            # Skip mutiple tracks and out of range
            elif amount is not None and amount > len(self.music_queue[guild_id]) - (self.current_music_queue_index[guild_id] + 1):
                self.current_music_queue_index[guild_id] += len(self.music_queue[guild_id]) - (self.current_music_queue_index[guild_id] + 1) - 1
                skip_embed.add_field(name="", value="The amount of tracks you tried to skip exceeded the total number of available tracks can be skipped in the queue. Automatically skipping to the last track in the queue...", inline=False)
            # Skip the current playing track
            else:
                skip_embed.add_field(name="", value="Skipped the current track", inline=False)
            # Stop the current song and plays the next song in queue if exsist
            self.vc[guild_id].stop()
            await interaction.response.send_message(embed=skip_embed)

    # Plays the previous track in the queue
    @commands.slash_command(name="previous", description="Plays the previous track in the queue")
    async def previous(self, interaction: Interaction):
        guild_id = interaction.guild.id
        prev_embed = discord.Embed(title="", color=interaction.author.colour)
        if self.vc[guild_id] != None and self.vc[guild_id]:
            # Try to play last in the queue if it exists
            if self.current_music_queue_index[guild_id] == 0:
                prev_embed.add_field(name="", value="There is no previous track in the queue.", inline=False)
            else:
                self.vc[guild_id].pause()
                self.current_music_queue_index[guild_id] -= 1
                await self.play_music(interaction)
                prev_embed.add_field(name="", value="Playing previous track...", inline=False)
        await interaction.response.send_message(embed=prev_embed)

    # Displays the current tracks in queue
    @commands.slash_command(name="queue", description="Displays the current tracks in queue")
    async def queue(self, interaction: Interaction):
        guild_id = interaction.guild.id
        queue_embed = discord.Embed(title="Queue:", color=interaction.author.colour)
        if self.music_queue[guild_id] != []:
            retval = ""
            # Get all tracks upcoming to play
            for next_track_index in range(self.current_music_queue_index[guild_id] + 1, len(self.music_queue[guild_id])):
                    retval += f"**#{1 + next_track_index}** - " + self.music_queue[guild_id][next_track_index][0]['title'] + "\n"
            if retval != "":
                # Return the track that currently playing and all upcoming tracks normally
                queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{self.current_music_queue_index[guild_id] + 1}** - {self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['title']}", inline=False)
                queue_embed.add_field(name="Upcoming tracks:", value=retval, inline=False)
            elif self.current_music_queue_index[guild_id] == len(self.music_queue[guild_id]):
                # Returns nothing if the queue has been ended
                queue_embed.add_field(name="Now Playing :notes: :", value=f"There are no tracks playing now", inline=False)
                queue_embed.add_field(name="Upcoming tracks:", value="There are no upcoming tracks will be played", inline=False)
            else:
                # Return the track that currently playing if that track was the last track in the queue
                queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{self.current_music_queue_index[guild_id] + 1}** - {self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['title']}", inline=False)
                queue_embed.add_field(name="Upcoming tracks:", value="There are no upcoming tracks will be played", inline=False)
        else:
            # Returns nothing if the queue was empty
            queue_embed.add_field(name="", value="There are no tracks in the queue", inline=False)
        await interaction.response.send_message(embed=queue_embed)

    # Stops the track currently playing and clears the queue
    @commands.slash_command(name="clear", description="Stops the track currently playing and clears the queue")
    async def clear(self, interaction: Interaction):
        guild_id = interaction.guild.id
        clear_embed = discord.Embed(title="Queue:", color=interaction.author.colour)
        self.music_queue[guild_id] = []
        if self.vc[guild_id] != None and self.is_playing[guild_id]:
            self.vc[guild_id].stop()
        self.current_music_queue_index[guild_id] == 0
        clear_embed.add_field(name="", value="Music queue has been cleared")
        await interaction.response.send_message(embed=clear_embed)
    
    # Removes the last or a specified track added to the queue
    @commands.slash_command(name="remove", description="Removes the last or a specified track added to the queue")
    async def remove(self, interaction: Interaction, position: Option(int, min = 1, description="Postion of track to remove. Leave this blank if you want to remove the last track.", required=False)):
        guild_id = interaction.guild.id
        remove_embed = discord.Embed(title="", color=interaction.author.colour)
        position = position or len(self.music_queue[guild_id])
        if position > len(self.music_queue[guild_id]):
            remove_embed.add_field(name="", value=f"Please enter a valid position of the track you want to remove from the queue.", inline=False)
        else:
            if position - 1 < 0:
                self.music_queue[guild_id].pop(0)
            else:
                self.music_queue[guild_id].pop(position - 1)
            remove_embed.add_field(name="", value=f"**#{position}** has been removed from queue.", inline=False)
        if (self.current_music_queue_index[guild_id] + 1) > position:
            self.current_music_queue_index[guild_id] -= 1
        await interaction.response.send_message(embed=remove_embed)

    # Joining voice channel
    @commands.slash_command(description="Invokes me to a voice channel")
    async def join(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to join. Leave this blank if you want the bot to join where you are.", required=False)):
        if interaction.author.voice is not None:
            if channel is not None:
                author_vc = channel
            else:
                author_vc = interaction.author.voice.channel
            voice_state = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            # This allows for more functionality with voice channels
            if voice_state is None:
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
        guild_id = interaction.guild.id
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice is not None:
            # Disconnect the bot from voice channel if it has been connected
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False
            self.music_queue[guild_id] = []
            await voice.disconnect()
            await interaction.response.send_message("I left the voice channel.")
        else:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel ^_^.")

    '''

    # Pause an audio currently playing in voice channel
    @commands.slash_command(description="Pause an audio currently playing in voice channel")
    async def pause(self, interaction: Interaction):
        guild_id = interaction.guild.id
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        try:
            if voice.is_playing():
                self.is_paused[guild_id] = True
                self.is_playing[guild_id] = False
                voice.pause()
            else:
                await interaction.response.send_message("At the moment, there is no audio playing in the voice channel!")
        except AttributeError:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("At the moment, there is no audio playing in the voice channel or i'm not in a voice channel!")

    # Resume an paused audio in voice channel
    @commands.slash_command(description="Resume an paused audio in voice channel")
    async def resume(self, interaction: Interaction):
        guild_id = interaction.guild.id
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        try:
            if voice.is_paused():
                voice.resume()
                self.is_playing[guild_id] = True
                self.is_paused[guild_id] = False
            else:
                await interaction.response.send_message("At the moment, no audio was paused!")
        except AttributeError:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("At the moment, no audio was paused or i'm not in a voice channel!")

    # Stops playing audio and leave voice
    @commands.slash_command(description="Stops playing audio")
    async def stop(self, interaction: Interaction):
        guild_id = interaction.guild.id
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        try:
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False
            self.music_queue[guild_id] = []
            voice.stop()
        except AttributeError:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel!")

    '''            

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
    async def move_all(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to move them to. Leave this blank if you want to move them into where you are.", required=False), reason: Option(str, description="Reason for move", required=False)):
        while True:
            if channel is None:
                if interaction.author.voice is not None:
                    specified_vc = interaction.author.voice.channel
                else:
                    # The author has not joined the voice channel yet
                    await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move all connected members into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move them into right now, <@{interaction.author.id}>？''')
                    break
            else:
                specified_vc = channel
            await self.move_all_members(interaction, specified_vc, reason=reason)
            break

    @move_all.error
    async def move_all_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move all users!")
        else:
            raise error

    # Move an user to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="user", description="Moves a member to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    async def move_user(self, interaction: Interaction, member: Option(discord.Member, description="User to move", required=True), channel: Option(discord.VoiceChannel, description="Channel to move user to. Leave this blank if you want to move the user into where you are.", required=False), reason: Option(str, description="Reason for move", required=False)):
        while True:
            if channel is None:
                if interaction.author.voice is not None:
                    specified_vc = interaction.author.voice.channel
                else:
                    # The author has not joined the voice channel yet
                    await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move someone into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move <@{member.id}> into right now, <@{interaction.author.id}>？''')
                    break
            else:
                specified_vc = channel
            if reason is None:
                await member.move_to(specified_vc)
                await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> by <@{interaction.author.id}>.")
            else:
                await member.move_to(specified_vc, reason=reason)
                await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> by <@{interaction.author.id}> for **{reason}**")
            break

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
        
    # Moves the bot to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="bot", description="Moves me to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(moderate_members=True)
    async def move_bot(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to move me to. Leave this blank if you want to move me into where you are.", required=False), reason: Option(str, description="Reason for move", required=False)):
        while True:
            if channel is None:
                if interaction.author.voice is not None:
                    specified_vc = interaction.author.voice.channel
                else:
                    # The author has not joined the voice channel yet
                    await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move me into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move into right now, <@{interaction.author.id}>？''')
                    break
            else:
                specified_vc = channel
            guild = self.bot.get_guild(interaction.guild.id)
            bot_member = guild.get_member(self.bot.application_id)
            if reason is None:
                await bot_member.move_to(specified_vc)
                await interaction.response.send_message(f"I moved to <#{specified_vc.id}>.")
            else:
                await bot_member.move_to(specified_vc, reason=reason)
                await interaction.response.send_message(f"I moved to <#{specified_vc.id}> for {reason}")
                break

    @move_bot.error
    async def move_bot_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move me!")
        else:
            raise error

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

    # Start the recording of a voice channel which the author is already connected, or a specified voice channel.    
    @commands.slash_command(description="Start the recording of a voice channel")
    async def start(self, interaction: Interaction, channel: Option(discord.VoiceChannel, description="Channel to record. Leave this blank if you want the bot to record where you are.", required=False)):
        await interaction.response.defer()
        if interaction.author.voice is not None:
            guild_id = interaction.guild.id
            if self.is_recording[guild_id]:
                return await interaction.followup.send("The recording was already started!")
            channel = channel or interaction.author.voice.channel

            self.rec_vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if self.rec_vc[guild_id] is None:
                self.rec_vc[guild_id] = await channel.connect()
            else:
                guild = self.bot.get_guild(interaction.guild.id)
                bot_member = guild.get_member(self.bot.application_id)
                self.rec_vc[guild_id] = await bot_member.move_to(channel)
            self.is_recording[guild_id] = True
            self.rec_vc[guild_id].start_recording(
            discord.sinks.OGGSink(),  # The sink type to use.
            self.finished_callback,  # What to do once done.
            interaction)
            await interaction.followup.send("The recording has been started!")
        else:
            await interaction.followup.send("Connect to a voice channel first.")

    # Stop the recording of a voice channel
    @commands.slash_command(description="Stop the recording of a voice channel")
    async def finish(self, interaction: Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild.id
        if guild_id in self.rec.vc and self.is_recording[guild_id]:
            await interaction.followup.send(f"Saving audio...", delete_after=1)
            self.rec_vc[guild_id].stop_recording()
            self.is_recording[guild_id] = False
            del self.rec_vc[guild_id]
        else:
            await interaction.followup.send("Not recording audio in this guild.")

    # ----------</Voice Channels>----------


def setup(bot):
    bot.add_cog(VoiceChannel(bot))
