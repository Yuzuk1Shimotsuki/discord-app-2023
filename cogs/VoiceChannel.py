import discord
import os
import shutil
import asyncio
from discord import app_commands, Interaction, FFmpegPCMAudio
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from tinytag import TinyTag
from typing import Optional, List

# Custom Errors
class AuthorNotInVoiceError():
    def __init__(self, interaction: Interaction, user: discord.User):
        self.user = user
        self.interaction = interaction
    def return_embed(self):
        embed = discord.Embed(title="", color=self.interaction.user.colour)
        embed.add_field(name="", value=f"<@{self.user.id}> Join a voice channel first plz :pleading_face:", inline=False)
        return embed

class BotAlreadyInVoiceError():
    def __init__(self, bot_vc, user_vc):
        self.bot_vc = bot_vc
        self.user_vc = user_vc
    def notauthor(self):
        return f'''I've already joined the voice channel :D , but not where you are ~
**I'm currently in:** <#{self.bot_vc.id}>
**You're currently in:** <#{self.user_vc.id}>'''
    def notrequired(self):
        return f'''I've already joined the voice channel :D , but not the required one ~
**I'm currently in:** <#{self.bot_vc.id}>
**The channel you wanted me to join:** <#{self.user_vc.id}>'''
    def same(self):
        return f"Can u found me in the voice channel？ I have connected to  <#{self.user_vc.id}> already :>"


# Main cog
class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        # General init
        self.bot = bot
        self.fallback_channel = {}
        # Music playing from YT
        # all the music related stuff
        global audio_source
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
        self.recording_vc = {}

    move = app_commands.Group(name="move", description="Move User")

    # ----------<Voice Channels>-----------

    # Startup
    @commands.Cog.listener()

    async def on_ready(self):
        for guild in self.bot.guilds:
            guild_id = int(guild.id)
            # 2d array containing [song, filetype]
            self.fallback_channel[guild_id] = None
            self.music_queue[guild_id] = []
            self.current_music_queue_index[guild_id] = 0
            self.vc[guild_id] = None
            self.is_paused[guild_id] = self.is_playing[guild_id] = False
            self.recording_vc[guild_id] = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member != self.bot.user:
            return
        vc = member.guild.voice_client
        
        """

        # Ensure:
        # - this is a channel move as opposed to anything else
        # - this is our instance's voice client and we can action upon it
        # Actions:
        # - Callback function when the bot moves from a voice channel to another voice channel
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
            # The bot has been moved and plays the original music again, there is no sense to execute the rest of statements.
            return

        """

        # Ensure:
        # - this is a channel leave as opposed to anything else
        # Actions:
        # - Reset all settings if the bot leave or being kicked by someone else
        if (
            after.channel is None and  # if this is None this is certainly a leave
            before.channel != after.channel  # if these match then this could be e.g. server deafen
        ):
            guild_id = before.channel.guild.id
            # To ensure the bot actually left the voice channel
            if self.fallback_channel[guild_id] is not None:
                await self.fallback_channel[guild_id].send("I left the voice channel.", silent=True)
            # Reset all settings on guild
            self.fallback_channel[guild_id] = None
            self.music_queue[guild_id] = []
            self.current_music_queue_index[guild_id] = 0
            self.vc[guild_id] = None
            self.is_paused[guild_id] = self.is_playing[guild_id] = False
            self.recording_vc[guild_id] = None
            guild_custom_dir = f"plugins/custom_audio/guild/{guild_id}"
            if os.path.exists(guild_custom_dir):
                shutil.rmtree(guild_custom_dir)
            return

    # Music Player

    # YouTube
    # Searching required item on YouTube
    def search_yt(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=False)["title"]
            return {'source':item, 'title':title}
        search = VideosSearch(item, limit=10)
        return {'source':search.result()["result"][0]["link"], 'title':search.result()["result"][0]["title"]}

    # Custom files
    # Fetching raw data from custom file
    async def fetch_custom_rawfile(self, interaction: Interaction, attachment: discord.Attachment):
        try:
            guild_id = interaction.guild.id
            print(attachment.content_type)
            supported_type = {"audio/mpeg": "mp3", "audio/x-wav": "wav", "audio/flac": "flac", "audio/mp4": "m4a"}
            if attachment.content_type in supported_type:
                extension = supported_type[attachment.content_type]
            else:
                # Unsupportted file
                return "!error%!unsupportted_file_type%"
            guild_dir = f"plugins/custom_audio/guild"
            if os.path.exists(f"{guild_dir}/{guild_id}") is False:
                path = os.path.join(guild_dir, str(guild_id))
                os.mkdir(path)
            audio_path = f"{guild_dir}/{guild_id}/audio{len(self.music_queue[guild_id])}.{extension}"
            await attachment.save(audio_path, use_cached=False)
            audiofile = TinyTag.get(audio_path)
            audio_artist =  audiofile.artist or "<Unknown artist>"
            audio_title = audiofile.title or "<Unknown title>"
            year = audiofile.year
            if audiofile.title is None and audiofile.artist is None:
                filename = attachment.filename.replace("_", " ")
            elif year is None:
                filename = f"{audio_artist} - {audio_title}"
            else:
                filename = f"{audio_artist} - {audio_title} ({year})"
            return {"source": attachment, "filename": filename, "audio_path": audio_path, "title": audiofile.title, "artist": audiofile.artist, "album": audiofile.album, "album_artist": audiofile.albumartist, "track_number": audiofile.track, "filesize": audiofile.filesize, "duration": audiofile.duration, "year": audiofile.year}
        except discord.errors.HTTPException as e:
            if e.status == 413:
                return "!error%!payload_too_large%"
            else:
                raise e

    # Infinite loop checking 
    async def auto_play_next(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if self.current_music_queue_index[guild_id] < len(self.music_queue[guild_id]):
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            self.current_music_queue_index[guild_id] += 1
            if self.music_queue[guild_id][self.current_music_queue_index[guild_id]][1] == "yt":
                raw_track = self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]["source"]
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(raw_track, download=False))
                source = data['url']
                before_options = self.FFMPEG_OPTIONS["before_options"]
                options = self.FFMPEG_OPTIONS["options"]
            else:
                source = self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]["audio_path"]
                before_options = options = None
            self.vc[guild_id].play(FFmpegPCMAudio(source, before_options=before_options, options=options), after=lambda e: asyncio.run_coroutine_threadsafe(self.auto_play_next(interaction), self.bot.loop))
        else:
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False

    # Function to play music
    async def play_music(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if self.current_music_queue_index[guild_id] < len(self.music_queue[guild_id]):
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            if self.music_queue[guild_id][self.current_music_queue_index[guild_id]][1] == "yt":
                raw_track = self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]["source"]
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(raw_track, download=False))
                source = data['url']
                before_options = self.FFMPEG_OPTIONS["before_options"]
                options = self.FFMPEG_OPTIONS["options"]
            else:
                source = self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]["audio_path"]
                before_options = options = None
            if self.vc[guild_id] is None:
                self.vc[guild_id] = await interaction.user.voice.channel.connect()
                self.fallback_channel[guild_id] = interaction.channel
                print(self.fallback_channel[guild_id])
            self.vc[guild_id].play(FFmpegPCMAudio(source, before_options=before_options, options=options), after=lambda e: asyncio.run_coroutine_threadsafe(self.auto_play_next(interaction), self.bot.loop))
        else:
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False


    # Discord Autocomplete for YouTube search, rewrited for discord.py
    async def yt_autocomplete(self,
        interaction: Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        if interaction.namespace.source == "yt":
            result_list = []
            if not current.startswith("https://"):
                try:
                    max_limit = 25
                    search = VideosSearch(current, limit=max_limit)
                    for i in range(max_limit):
                        try:
                            result_list.append(search.result()["result"][i]["title"])
                        except IndexError:
                            break
                    return [
                        app_commands.Choice(name=video, value=video)
                        for video in result_list if current.lower() in video.lower()
                    ]
                except TypeError:
                    # The author did not entered anything yet
                    # Originally it should return a defult list on Windows, not sure why it's not working on linux...
                    return []
            return []
        else:
            # The source is not from YouTube
            return []

    # Play selected tracks
    @app_commands.command(description="Adds a selected track to the queue from YouTube link, keywords or a local file")
    @app_commands.describe(source="Source to play the track on")
    @app_commands.describe(query="Link or keywords of the track you want to play.")
    @app_commands.describe(attachment="The track to be played.")
    @app_commands.choices(source=[app_commands.Choice(name="YouTube", value="yt"),
                                 app_commands.Choice(name="Custom files", value="custom")
                                 ])
    @app_commands.autocomplete(query=yt_autocomplete)
    async def play(self, interaction:Interaction, source: app_commands.Choice[str], query: Optional[str] = None, attachment: Optional[discord.Attachment] = None):
        guild_id = interaction.guild.id
        play_embed = discord.Embed(title="", color=interaction.user.colour)
        try:
            self.vc[guild_id] = self.vc[guild_id] or interaction.user.voice.channel
        except:
            return await interaction.response.send_message(embed=AuthorNotInVoiceError(interaction, interaction.user).return_embed())
        await interaction.response.defer()
        if self.vc[guild_id] is not None and self.is_paused[guild_id]:
                self.vc[guild_id].resume()
        elif self.vc[guild_id] is not None:
            if source.value == "yt":
                # From YouTube
                if query is None:
                    play_embed.add_field(name="", value=f'''Looks like you've selected YouTube as the audio source, but haven't specified the track you would like to play :thinking: ...
Just curious to know, what should I play right now, <@{interaction.user.id}>？''', inline=False)
                    return await interaction.followup.send(embed=play_embed)
                track = self.search_yt(query)
                track_title = track['title']
                if type(track) == type(True):
                    play_embed.add_field(name="", value="Could not download the song: Incorrect format. Try another keywords. This could be due to the link you entered is a playlist or livestream format.", inline=False)
                    return await interaction.followup.send(embed=play_embed)
            elif source.value == "custom":
                # Custom file
                if attachment is None:
                    play_embed.add_field(name="", value=f'''Looks like you've selected custom as the audio source, but haven't specified the file you would like to play :thinking: ...
Just curious to know, what should I play right now, <@{interaction.user.id}>？''', inline=False)
                    return await interaction.followup.send(embed=play_embed)
                track = await self.fetch_custom_rawfile(interaction, attachment)
                # Return errors if occurs, or proceed to the next step if no errors encountered
                if track == "!error%!payload_too_large%":
                    play_embed.add_field(name="", value=f"Yooo, The file you uploaded was too large! I can't handle it apparently...", inline=False)
                    return await interaction.followup.send(embed=play_embed)
                elif track == "!error%!unsupportted_file_type%":
                    play_embed.add_field(name="", value=f"Looks like the file you uploaded has an unsupportted format :thinking: ... Perhaps try to upload another file and gave me a chance to handle it？", inline=False)
                    return await interaction.followup.send(embed=play_embed)
                track_title = track["filename"]
            if self.is_playing[guild_id]:
                play_embed.add_field(name="", value=f"**#{1 + len(self.music_queue[guild_id])} - '{track_title}'** added to the queue", inline=False)
            else:
                play_embed.add_field(name="", value=f"**'{track_title}'** added to the queue", inline=False)
            self.music_queue[guild_id].append([track, source.value])
            await interaction.followup.send(embed=play_embed)
            if self.is_playing[guild_id] == False:
                self.current_music_queue_index[guild_id] = 0
                await self.play_music(interaction)
        else:
            await interaction.response.send_message(embed=AuthorNotInVoiceError(interaction, interaction.user).return_embed())

    # Pauses the current track
    @app_commands.command(name="pause", description="Pauses the current track being played in voice channel")
    async def pause(self, interaction: Interaction):
        guild_id = interaction.guild.id
        pause_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is not None:
            if self.is_playing[guild_id] and not self.is_paused[guild_id]:
                self.is_playing[guild_id] = False
                self.is_paused[guild_id] = True
                self.vc[guild_id].pause()
                pause_embed.add_field(name="", value="The track has been paused.", inline=False)
            elif self.is_paused[guild_id] and not self.is_playing[guild_id]:
                pause_embed.add_field(name="", value="The track has been already paused!", inline=False)
            else:
                pause_embed.add_field(name="", value="No track was playing in voice channel.", inline=False)
        else:
            pause_embed.add_field(name="", value="No track was playing. I'm not even in a voice channel.", inline=False)
        await interaction.response.send_message(embed=pause_embed)

    # Resume a paused track
    @app_commands.command(name = "resume", description="Resume a paused track in voice channel")
    async def resume(self, interaction: Interaction):
        guild_id = interaction.guild.id
        resume_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is not None:
            if self.is_paused[guild_id] and not self.is_playing[guild_id]:
                self.is_paused[guild_id] = False
                self.is_playing[guild_id] = True
                self.vc[guild_id].resume()
                resume_embed.add_field(name="", value="Resuming the track...", inline=False)
            else:
                resume_embed.add_field(name="", value="No track has been paused before in voice channel.", inline=False)
        else:
            resume_embed.add_field(name="", value="No track has been paused before. I'm not even in a voice channel.", inline=False)
        await interaction.response.send_message(embed=resume_embed)
    
    # Skipping tracks
    @app_commands.command(name="skip", description="Skips the current track being played in voice channel")
    @app_commands.describe(amount="Number of track to skip. Leave this blank if you want to skip the current track only.")
    async def skip(self, interaction: Interaction, amount: Optional[app_commands.Range[int, 1]] = 1):
        guild_id = interaction.guild.id
        skip_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is not None:
            if self.current_music_queue_index[guild_id] > len(self.music_queue[guild_id]) - 1:
                # The author has been already gone through all tracks in the queue
                skip_embed.add_field(name="", value=f"<@{interaction.user.id}> You have already gone through all tracks in the queue.", inline=False)
            elif amount > len(self.music_queue[guild_id]) - (self.current_music_queue_index[guild_id]):
                # Auto skip to the last track as the required amount exceeded the total number of available tracks can be skipped in the queue
                self.current_music_queue_index[guild_id] += len(self.music_queue[guild_id]) - (self.current_music_queue_index[guild_id] + 1) - 1
                skip_embed.add_field(name="", value="The amount of tracks you tried to skip exceeded the total number of available tracks can be skipped in the queue. Automatically skipping to the last track in the queue...", inline=False)
            elif amount == len(self.music_queue[guild_id]) - (self.current_music_queue_index[guild_id]):
                # The author just skipped the final track
                skip_embed.add_field(name="", value=f"Skipped the final track. There are no upcoming tracks will be played.", inline=False)
            else:
                # Skip the required amount of tracks
                self.current_music_queue_index[guild_id] += amount - 1
                if amount > 1:
                    skip_embed.add_field(name="", value=f"Skipped **{amount}** tracks in the queue", inline=False)
                else:
                    skip_embed.add_field(name="", value="Skipped the current track", inline=False)
            self.vc[guild_id].stop()
        else:
            skip_embed.add_field(name="", value="I'm not in a voice channel.", inline=False)
        await interaction.response.send_message(embed=skip_embed)

    # Playing previous track or rolling back multiple tracks
    @app_commands.command(name="previous", description="Plays the previous track in the queue")
    @app_commands.describe(amount="Number of tracks to be rollback. Leave this blank if you want to play the previous track only.")
    async def previous(self, interaction: Interaction, amount: Optional[app_commands.Range[int, 1]] = 1):
        guild_id = interaction.guild.id
        prev_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is not None:
            if self.current_music_queue_index[guild_id] == 0:
                prev_embed.add_field(name="", value="There is no previous track in the queue.", inline=False)
            else:
                # Try to rollback the required amount of tracks in the queue if exists
                self.vc[guild_id].pause()
                # Executes when out of range
                if self.current_music_queue_index[guild_id] - amount < 0:
                    self.current_music_queue_index[guild_id] = 0
                    prev_embed.add_field(name="", value="The amount of tracks you tried to rollback exceeded the total number of available tracks can be rollback in the queue. Automatically rollback to the beginning track in the queue...", inline=False)
                else:
                    # Rollback the required amount of tracks
                    self.current_music_queue_index[guild_id] -= amount
                    if amount > 1:
                        prev_embed.add_field(name="", value=f"Rolling back **{amount}** tracks from the current track...", inline=False)
                    else:
                        prev_embed.add_field(name="", value="Playing previous track...", inline=False)
                await self.play_music(interaction)
        else:
            prev_embed.add_field(name="", value="There is no previous track in the queue. I'm not even in a voice channel.", inline=False)
        await interaction.response.send_message(embed=prev_embed)
        
    # Shows the queue
    @app_commands.command(name="queue", description="Shows the queue in this server")
    async def queue(self, interaction: Interaction):
        guild_id = interaction.guild.id
        queue_embed = discord.Embed(title="Queue:", color=interaction.user.colour)
        if self.music_queue[guild_id] != []:
            retval = ""
            # Get all tracks upcoming to play
            for next_track_index in range(self.current_music_queue_index[guild_id] + 1, len(self.music_queue[guild_id])):
                if self.music_queue[guild_id][next_track_index][1] == "yt":
                    # From YouTube
                    retval += f"**#{1 + next_track_index}** - " + self.music_queue[guild_id][next_track_index][0]['title'] + "\n"
                else:
                    # Custom file
                    retval += f"**#{1 + next_track_index}** - " + self.music_queue[guild_id][next_track_index][0]['filename'] + "\n"
            if retval != "":
                # Return the track that currently playing and all upcoming tracks normally
                if self.music_queue[guild_id][self.current_music_queue_index[guild_id]][1] == "yt":
                    # From YouTube
                    queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{self.current_music_queue_index[guild_id] + 1}** - {self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['title']}", inline=False)
                else:
                    # Custom file
                    queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{self.current_music_queue_index[guild_id] + 1}** - {self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['filename']}", inline=False)
                queue_embed.add_field(name="Upcoming tracks:", value=retval, inline=False)
            elif self.current_music_queue_index[guild_id] == len(self.music_queue[guild_id]):
                # Returns nothing if the queue has been ended
                queue_embed.add_field(name="Now Playing :notes: :", value=f"There are no tracks playing now", inline=False)
                queue_embed.add_field(name="Upcoming tracks:", value="There are no upcoming tracks will be played", inline=False)
            else:
                # Return the track that currently playing if that track was the last track in the queue
                if self.music_queue[guild_id][self.current_music_queue_index[guild_id]][1] == "yt":
                    # From YouTube
                    queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{self.current_music_queue_index[guild_id] + 1}** - {self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['title']}", inline=False)
                else:
                    # Custom file
                    queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{self.current_music_queue_index[guild_id] + 1}** - {self.music_queue[guild_id][self.current_music_queue_index[guild_id]][0]['filename']}", inline=False)
                queue_embed.add_field(name="Upcoming tracks:", value="There are no upcoming tracks will be played", inline=False)
        else:
            # Returns nothing if the queue was empty
            queue_embed.add_field(name="", value="There are no tracks in the queue", inline=False)
        await interaction.response.send_message(embed=queue_embed)

    # Stops the track currently playing and clears the queue
    @app_commands.command(name="clear", description="Stops the track currently playing and clears the queue")
    async def clear(self, interaction: Interaction):
        guild_id = interaction.guild.id
        clear_embed = discord.Embed(title="Queue:", color=interaction.user.colour)
        if self.music_queue[guild_id] != []:
            self.music_queue[guild_id] = []
            if self.vc[guild_id] is not None and self.is_playing[guild_id]:
                self.is_playing[guild_id] = False
                self.is_paused[guild_id] = False
                self.vc[guild_id].stop()
                guild_custom_dir = f"plugins/custom_audio/guild/{guild_id}"
                if os.name == "nt":
                    # Kill ffmpeg.exe before remove the directory in Windows to prevent error
                    # No need to do this in linux
                    os.system("taskkill /im ffmpeg.exe /f")
                if os.path.exists(guild_custom_dir):
                    shutil.rmtree(guild_custom_dir)
            self.current_music_queue_index[guild_id] == 0
            clear_embed.add_field(name="", value="Music queue has been cleared.")
        else:
            clear_embed.add_field(name="", value="There are no tracks in the queue")
        await interaction.response.send_message(embed=clear_embed)

    # Removes the last or a specified track added to the queue
    @app_commands.command(name="remove", description="Removes the last or a specified track added to the queue")
    @app_commands.describe(position="Postion of track to remove. Leave this blank if you want to remove the last track.")
    async def remove(self, interaction: Interaction, position: Optional[app_commands.Range[int, 1]] = None):
        guild_id = interaction.guild.id
        remove_embed = discord.Embed(title="Queue", color=interaction.user.colour)
        if self.music_queue[guild_id] != []:
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
            guild_custom_dir = f"plugins/custom_audio/guild/{guild_id}"
            for track in self.music_queue[guild_id]:
                renewed_index = 0
                if track[1] == "Custom file":
                    if os.name == "nt":
                        os.system("taskkill /im ffmpeg.exe /f")
                    try:
                        os.rename(f"{track[0]['audio_path']}", f"{track[0]['audio_path'][:-5]}{renewed_index}{track[0]['audio_path'][-4:]}")
                    except FileExistsError:
                        pass
                    print("test")
                renewed_index += 1
        else:
            remove_embed.add_field(name="", value="There are no tracks in the queue")
        await interaction.response.send_message(embed=remove_embed)


    # General commands

    # Joining voice channel
    @app_commands.command(description="Invokes me to a voice channel")
    @app_commands.describe(channel="Channel to join. Leave this blank if you want the bot to join where you are.")
    async def join(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None):
        guild_id = interaction.guild.id
        if interaction.user.voice is not None:
            voice_channel = channel or interaction.user.voice.channel
            self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            # This allows for more functionality with voice channels
            if self.vc[guild_id] is None:
                # None being the default value if the bot isnt in a channel (which is why the is_connected() is returning errors)
                # Connect the bot to voice channel
                self.vc[guild_id] = await voice_channel.connect()
                await interaction.response.send_message(f"I joined the voice channel <#{voice_channel.id}>")
                self.fallback_channel[guild_id] = interaction.channel
            elif self.vc[guild_id].channel.id != voice_channel.id:
                # The bot has been connected to a voice channel but not as same as the author or required one
                if channel is not None:
                    # The bot has been connected to a voice channel but not as same as the required one
                    await interaction.response.send_message(BotAlreadyInVoiceError(self.vc[guild_id].channel, voice_channel).notrequired())
                else:
                    # The bot has been connected to a voice channel but not as same as the author one
                    await interaction.response.send_message(BotAlreadyInVoiceError(self.vc[guild_id].channel, voice_channel).notauthor())
            else:
                # The bot has been connected to the same channel as the author
                await interaction.response.send_message(BotAlreadyInVoiceError(voice_channel, voice_channel).same())
        else:
            # The author has not joined the voice channel yet
            await interaction.response.send_message(embed=AuthorNotInVoiceError(interaction, interaction.author).return_embed())

    # Leaving voice channel
    @app_commands.command(description="Leaving a voice channel")
    async def leave(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if self.vc[guild_id] is not None:
            # Disconnect the bot from voice channel if it has been connected
            await self.vc[guild_id].disconnect()
            await interaction.response.send_message("Leaving...", ephemeral=True, delete_after=0)
        else:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel ^_^.")

    # Ends a voice call

    # Function to end a voice call
    async def end_voice_call(self, interaction: Interaction):
        guild_id = interaction.guild.id
        # Disconnect the bot from voice channel if it has been connected
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if self.vc[guild_id] is not None:
            await self.vc[guild_id].disconnect()
        # Disconnect the members from voice channel if they are connected
        for member in interaction.guild.members:
            if member.voice is not None:
                await member.move_to(None)

    # Ending a voice call
    @app_commands.command(name="end", description="End the call for all voice channels")
    @app_commands.checks.has_permissions(move_members=True)
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
    @app_commands.checks.has_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move them to. Leave this blank if you want to move them into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_all(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        while True:
            if channel is None:
                if interaction.user.voice is not None:
                    specified_vc = interaction.user.voice.channel
                else:
                    # The author has not joined the voice channel yet
                    await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move all connected members into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move them into right now, <@{interaction.user.id}>？''')
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
    @app_commands.describe(member="Member to move")
    @app_commands.describe(channel="Channel to move user to. Leave this blank if you want to move the user into where you are.")
    @app_commands.describe(reason="Reason for move")
    @commands.has_guild_permissions(move_members=True)
    async def move_user(self, interaction: Interaction, member: discord.Member, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        while True:
            if channel is None:
                if interaction.user.voice is not None:
                    specified_vc = interaction.user.voice.channel
                else:
                    # The author has not joined the voice channel yet
                    await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move someone into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move <@{member.id}> into right now, <@{interaction.user.id}>？''')
                    break
            else:
                specified_vc = channel
            if reason is None:
                await member.move_to(specified_vc)
                await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> by <@{interaction.user.id}>.")
            else:
                await member.move_to(specified_vc, reason=reason)
                await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> by <@{interaction.user.id}> for **{reason}**")
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
    @app_commands.describe(channel="Channel to move you to.")
    @app_commands.describe(reason="Reason for move")
    async def move_me(self, interaction: Interaction, channel: discord.VoiceChannel, reason: Optional[str] = None):
        if reason is None:
            await interaction.user.move_to(channel)
            await interaction.response.send_message(f"<@{interaction.user.id}> has been moved to <#{channel.id}>.")
        else:
            await interaction.user.move_to(channel, reason=reason)
            await interaction.response.send_message(f"<@{interaction.user.id}> has been moved to <#{channel.id}> for {reason}")

    @move_me.error
    async def move_me_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move!")
        else:
            raise error
        
    # Moves the bot to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="bot", description="Moves me to another specified voice channel")
    @app_commands.checks.has_permissions(move_members=True, moderate_members=True)
    @app_commands.describe(channel="Channel to move me to. Leave this blank if you want to move me into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_bot(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        while True:
            if channel is None:
                if interaction.author.voice is not None:
                    specified_vc = interaction.author.voice.channel
                else:
                    # The author has not joined the voice channel yet
                    await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move me into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move into right now, <@{interaction.user.id}>？''')
                    break
            else:
                specified_vc = channel
            # Getting bot member as a 'Member' object instead of 'ClientUser' object (which is why the bot.user is returning errors)
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
