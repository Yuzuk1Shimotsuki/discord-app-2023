import discord
import os
import math
import shutil
import asyncio
from discord import app_commands, Interaction, FFmpegPCMAudio, PCMVolumeTransformer, SelectOption
from discord.ext import commands
from discord.ui import Select, View
from discord.app_commands.errors import MissingPermissions
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
from tinytag import TinyTag
from typing import Optional, List
from ErrorHandling import *

selectlist = []
tracks_per_page = 15  # Should not exceed 20 (Theocratically it should be able to exceed 23, but we limited it to 20 just in case.)
# or it will raise HTTPException: 400 Bad Request (error code: 50035): Invalid Form Body In data.embeds.0.fields.1.value: Must be 1024 or fewer in length.

current_track_queue_index = {}
track_queue = {}
repeat_one = {}
repeat_all = {}

# Page select for track queue
class MySelect(Select):
    def __init__(self):
        global selectlist
        global tracks_per_page
        global current_track_queue_index
        global track_queue
        global repeat_one
        global repeat_all
        
        options = selectlist
        super().__init__(placeholder="Page", min_values=1, max_values=1, options=options)

    # Callback for the page select dropdown
    async def callback(self, interaction):
        guild_id = interaction.guild.id
        page = int(self.values[0])
        # Refresh page
        # 1st page
        total_page = math.ceil(float((len(track_queue[guild_id]) - current_track_queue_index[guild_id]) / tracks_per_page))
        start = current_track_queue_index[guild_id] + 1
        if len(track_queue[guild_id]) - current_track_queue_index[guild_id] - 1 > tracks_per_page:
            end = current_track_queue_index[guild_id] + 1 + tracks_per_page
        else:
            end = len(track_queue[guild_id])
        global_selectlist = []
        global_selectlist.append(discord.SelectOption(label=f"1", value=f"1", description=f"{start} - {end}"))
        if len(track_queue[guild_id]) - current_track_queue_index[guild_id] - 1 > tracks_per_page:
            # 2nd and so on
            for i in range(2, total_page + 1):
                start = 1 + end
                end = start + tracks_per_page
                if start >= len(track_queue[guild_id]) + 1:
                    break
                if end > len(track_queue[guild_id]):
                    global_selectlist.append(discord.SelectOption(label=f"{i}", value=f"{i}", description=f"{start} - {len(track_queue[guild_id])}"))
                else:
                    global_selectlist.append(discord.SelectOption(label=f"{i}", value=f"{i}", description=f"{start} - {end}"))
        queue_embed = discord.Embed(title="Queue:", color=interaction.user.color)
        if page < 2:
            start = current_track_queue_index[guild_id] + 1 + tracks_per_page * (page - 1)
        else:
            start = current_track_queue_index[guild_id] + (page - 1) + tracks_per_page * (page - 1)
        end = current_track_queue_index[guild_id] + page + tracks_per_page * (page)
        retval = ""
        # Retrieving tracks
        # Get all tracks upcoming to play
        if track_queue[guild_id] == []:
            # Returns nothing if the queue was empty
            queue_embed.add_field(name="", value="There are no tracks in the queue", inline=False)
            view = None
        elif current_track_queue_index[guild_id] == len(track_queue[guild_id]):
            # Returns nothing if the queue has been ended
            queue_embed.add_field(name=f"Now Playing :notes: :", value=f"There are no tracks playing now", inline=False)
            queue_embed.add_field(name="Upcoming Tracks:", value="There are no upcoming tracks will be played", inline=False)
            view = None
        elif current_track_queue_index[guild_id] + 1 == len(track_queue[guild_id]):
            # Return the track that currently playing if that track was the last track in the queue
            if track_queue[guild_id][current_track_queue_index[guild_id]][1] == "yt":
                # From YouTube
                queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['title']}", inline=False)
            else:
                # Custom file
                queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['filename']}", inline=False)
            queue_embed.add_field(name="Upcoming Tracks:", value="There are no upcoming tracks will be played", inline=False)
            view = None
        else:
            if end > len(track_queue[guild_id]):
                end = len(track_queue[guild_id])
            retval = ""
            for next_track_index in range(start, end):
                if track_queue[guild_id][next_track_index][1] == "yt":
                    # From YouTube
                    retval += f"**#{1 + next_track_index}** - " + track_queue[guild_id][next_track_index][0]['title'] + "\n"
                else:
                    # Custom file
                    retval += f"**#{1 + next_track_index}** - " + track_queue[guild_id][next_track_index][0]['filename'] + "\n"
            # Return the track that currently playing and all upcoming tracks normally
            if track_queue[guild_id][current_track_queue_index[guild_id]][1] == "yt":
                # From YouTube
                queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['title']}", inline=False)
            else:
                # Custom file
                queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['filename']}", inline=False)
            queue_embed.add_field(name="Upcoming Tracks:", value=retval, inline=False)
            view = DropdownView()
        if repeat_one[guild_id]:
            queue_embed.add_field(name='\u200b', value="", inline=False)
            queue_embed.add_field(name='''"Repeat one" has been enabled.''', value="", inline=False)
        if repeat_all[guild_id]:
            queue_embed.add_field(name='\u200b', value="", inline=False)
            queue_embed.add_field(name='''"Repeat all" has been enabled.''', value="", inline=False)
        if view is None:
            await interaction.response.edit_message(embed=queue_embed)
        else:
            await interaction.response.edit_message(embed=queue_embed, view=view)

class DropdownView(View):
    def __init__(self):
        super().__init__()
        self.add_item(MySelect())


# Main cog
class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        # General init
        self.bot = bot
        self.fallback_channel = {}
        # Music playing from YT
        # all the music related stuff
        global selectlist
        global tracks_per_page
        global current_track_queue_index
        global track_queue
        global repeat_one
        global repeat_all
        self.is_playing = {}
        self.is_paused = {}
        self.player_volume = {}
        self.repeat_one = {}
        self.repeat_all = {}
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
            # Change glboally
            current_track_queue_index[guild_id] = 0
            track_queue[guild_id] = []
            # Change lacally
            self.fallback_channel[guild_id] = None
            self.is_paused[guild_id] = self.is_playing[guild_id] = False
            self.player_volume[guild_id] = 100  # 0 - 200%
            repeat_one[guild_id] = False
            repeat_all[guild_id] = False
            self.vc[guild_id] = None
            self.recording_vc[guild_id] = None


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):

        # Ensure:
        # - this is a channel leave as opposed to anything else
        # Actions:
        # - Reset all settings if the bot leave or being kicked by someone else

        if member != self.bot.user:
            return
        guild_channel = before.channel or after.channel
        guild = guild_channel.guild
        guild_id = guild_channel.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=guild)

        if (
            after.channel is None and  # if this is None this is certainly a leave
            before.channel != after.channel  # if these match then this could be e.g. server deafen
        ):
            guild_id = before.channel.guild.id
            # To ensure the bot actually left the voice channel
            self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=before.channel.guild)
            if self.vc[guild_id] is not None and self.is_playing[guild_id] is False:
                await self.vc[guild_id].disconnect()
            if self.fallback_channel[guild_id] is not None:
                await self.fallback_channel[guild_id].send("I left the voice channel.", silent=True)
            # Reset all settings on guild
            self.fallback_channel[guild_id] = None
            self.is_paused[guild_id] = self.is_playing[guild_id] = False
            current_track_queue_index[guild_id] = 0
            track_queue[guild_id] = []
            self.player_volume[guild_id] = 100  # 0 - 200%
            repeat_one[guild_id] = False
            repeat_all[guild_id] = False
            self.vc[guild_id] = None
            self.recording_vc[guild_id] = None
            guild_custom_dir = f"plugins/custom_audio/guild/{guild_id}"
            if os.path.exists(guild_custom_dir):
                shutil.rmtree(guild_custom_dir)

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
            audio_path = f"{guild_dir}/{guild_id}/audio{len(track_queue[guild_id])}.{extension}"
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

    # Auto plays the next track accordingly, with conditions.
    async def auto_play_next(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not repeat_one[guild_id]:
            current_track_queue_index[guild_id] += 1
        if current_track_queue_index[guild_id] < len(track_queue[guild_id]):
            self.is_playing[guild_id] = True
            self.is_paused[guild_id] = False
            if track_queue[guild_id][current_track_queue_index[guild_id]][1] == "yt":
                raw_track = track_queue[guild_id][current_track_queue_index[guild_id]][0]["source"]
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(raw_track, download=False))
                source = data['url']
                before_options = self.FFMPEG_OPTIONS["before_options"]
                options = self.FFMPEG_OPTIONS["options"]
            else:
                source = track_queue[guild_id][current_track_queue_index[guild_id]][0]["audio_path"]
                before_options = options = None
            # Loop 
            self.vc[guild_id].play(PCMVolumeTransformer(FFmpegPCMAudio(source, executable="C:\\FFmpeg\\ffmpeg.exe", before_options=before_options, options=options), volume=self.player_volume[guild_id] / 100), after=lambda e: asyncio.run_coroutine_threadsafe(self.auto_play_next(interaction), self.bot.loop))
        # Executed after the player gone through all the taracks
        # Normally the player will be stopped, except "repeat all" was set to True.
        elif repeat_all[guild_id]:
            # Repeat all tracks
            current_track_queue_index[guild_id] = 0
            await self.play_music(interaction)
        else:
            # Stops the player
            self.is_playing[guild_id] = False
            self.is_paused[guild_id] = False

    # Function to play music
    async def play_music(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        self.is_playing[guild_id] = True
        self.is_paused[guild_id] = False
        if track_queue[guild_id][current_track_queue_index[guild_id]][1] == "yt":
            raw_track = track_queue[guild_id][current_track_queue_index[guild_id]][0]["source"]
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(raw_track, download=False))
            source = data['url']
            before_options = self.FFMPEG_OPTIONS["before_options"]
            options = self.FFMPEG_OPTIONS["options"]
        else:
            source = track_queue[guild_id][current_track_queue_index[guild_id]][0]["audio_path"]
            before_options = options = None
        if self.vc[guild_id] is None:
            self.vc[guild_id] = await interaction.user.voice.channel.connect()
            self.fallback_channel[guild_id] = interaction.channel
        # Plays the track. After the track is played, it will be checked in coroutine "auto_play_next" for further operation.
        self.vc[guild_id].play(PCMVolumeTransformer(FFmpegPCMAudio(source, executable="C:\\FFmpeg\\ffmpeg.exe", before_options=before_options, options=options), volume=self.player_volume[guild_id] / 100), after=lambda e: asyncio.run_coroutine_threadsafe(self.auto_play_next(interaction), self.bot.loop))

    # Discord Autocomplete for YouTube search, rewrited for discord.py
    async def yt_autocomplete(self,
        interaction: Interaction,
        query: str
    ) -> List[app_commands.Choice[str]]:
        if interaction.namespace.source == "yt":
            result_list = []
            if not query.startswith("https://"):
                # Serach from keywords
                try:
                    max_limit = 25
                    search = VideosSearch(query, limit=max_limit)
                    for i in range(max_limit):
                        try:
                            result_list.append(search.result()["result"][i]["title"])
                        except IndexError:
                            break
                    return [
                        app_commands.Choice(name=video, value=video)
                        for video in result_list if query.lower() in video.lower()
                    ]
                except TypeError:
                    # The author did not entered anything yet
                    # Originally it should return a defult list on Windows, not sure why it's not working on linux...
                    return []
            # Reutrn a blank list because YouTube URL's does not required to be searched.
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
            # Append the audio to the queue
            for x in range(33):
                track_queue[guild_id].append([track, source.value])
            if len(track_queue[guild_id]) - 1 > 0:
                # The queue contains more than 1 audio
                play_embed.add_field(name="", value=f"**#{len(track_queue[guild_id])} - '{track_title}'** added to the queue", inline=False)
            else:
                # The queue only contains 1 audio
                play_embed.add_field(name="", value=f"**'{track_title}'** added to the queue", inline=False)
            await interaction.followup.send(embed=play_embed)
            # Starts from index 0 if the queue only contains 1 audio
            if len(track_queue[guild_id]) - 1 == 0:
                current_track_queue_index[guild_id] = 0
            # Plays the audio
            if not self.is_playing[guild_id]:
                await self.play_music(interaction)
        else:
            # The author is currently not in a voice channel
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
                pause_embed.add_field(name="", value="No tracks were playing in voice channel.", inline=False)
        else:
            pause_embed.add_field(name="", value="No tracks were playing. I'm not even in a voice channel.", inline=False)
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
            # Disable "repeat one" temporarily as it would affecting the entire process
            repeat_one_tmp = repeat_one[guild_id]
            repeat_one[guild_id] = False
            if current_track_queue_index[guild_id] > len(track_queue[guild_id]) - 1:
                # The author has been already gone through all tracks in the queue
                skip_embed.add_field(name="", value=f"<@{interaction.user.id}> You have already gone through all tracks in the queue.", inline=False)
            elif amount > len(track_queue[guild_id]) - (current_track_queue_index[guild_id]):
                # Auto skip to the last track as the required amount exceeded the total number of available tracks can be skipped in the queue
                current_track_queue_index[guild_id] += len(track_queue[guild_id]) - (current_track_queue_index[guild_id] + 1) - 1
                skip_embed.add_field(name="", value="The amount of tracks you tried to skip exceeded the total number of available tracks can be skipped in the queue. Automatically skipping to the last track in the queue...", inline=False)
            elif amount == len(track_queue[guild_id]) - (current_track_queue_index[guild_id]):
                # The author just skipped the final track
                skip_embed.add_field(name="", value=f'''Skipped the final track. There are no upcoming tracks will be played unless **"Repeat all"** was **enabled**.''', inline=False)
                current_track_queue_index[guild_id] += amount - 1
            else:
                # Skip the required amount of tracks
                current_track_queue_index[guild_id] += amount - 1
                if amount > 1:
                    skip_embed.add_field(name="", value=f"Skipped **{amount}** tracks in the queue", inline=False)
                else:
                    skip_embed.add_field(name="", value="Skipped the current track", inline=False)
            self.vc[guild_id].stop()
            if repeat_one_tmp:
            # Enable "repeat one" if it was enabled intentionally
                await asyncio.sleep(2)
                repeat_one[guild_id] = True
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
            if current_track_queue_index[guild_id] == 0:
                prev_embed.add_field(name="", value="There is no previous track in the queue.", inline=False)
            else:
                # Try to rollback the required amount of tracks in the queue if exists
                self.vc[guild_id].pause()
                # Executes when out of range
                if current_track_queue_index[guild_id] - amount < 0:
                    current_track_queue_index[guild_id] = 0
                    prev_embed.add_field(name="", value="The amount of tracks you tried to rollback exceeded the total number of available tracks can be rollback in the queue. Automatically rollback to the beginning track in the queue...", inline=False)
                else:
                    # Rollback the required amount of tracks
                    current_track_queue_index[guild_id] -= amount
                    if amount > 1:
                        prev_embed.add_field(name="", value=f"Rolling back **{amount}** tracks from the current track...", inline=False)
                    else:
                        prev_embed.add_field(name="", value="Playing previous track...", inline=False)
                await self.play_music(interaction)
        else:
            prev_embed.add_field(name="", value="There is no previous track in the queue. I'm not even in a voice channel.", inline=False)
        await interaction.response.send_message(embed=prev_embed)

    # Looping the current track or all tracks in the list
    @app_commands.command(name="repeat", description="Looping the current track or all tracks in the list")
    @app_commands.describe(type="The type to repeat (Can be the current track or all tracks)")
    @app_commands.choices(type=[app_commands.Choice(name="Repeat one", value="repeat_one"),
                                 app_commands.Choice(name="Repeat all", value="repeat_all")
                                 ])
    @app_commands.choices(option=[app_commands.Choice(name="Enable", value="true"),
                                 app_commands.Choice(name="Disable", value="false")
                                 ])
    async def repeat(self, interaction: Interaction, type: app_commands.Choice[str], option: app_commands.Choice[str]):
        guild_id = interaction.guild.id
        repeat_embed = discord.Embed(title="", color=interaction.user.colour)
        if type.value == "repeat_one":
            if repeat_one[guild_id] and option.value == "true":
                repeat_embed.add_field(name="", value=f'''**"Repeat one"** has been already **enabled**!''', inline=False)
            elif not repeat_one[guild_id] and option.value == "false":
                repeat_embed.add_field(name="", value=f'''**"Repeat one"** has been already **disabled**!''', inline=False)
            elif not repeat_one[guild_id] and option.value == "true":
                repeat_all[guild_id] = False
                repeat_one[guild_id] = True
                repeat_embed.add_field(name="", value=f'''**"Repeat one"** has been **enabled**.''', inline=False)
            elif repeat_one[guild_id] and option.value == "false":
                repeat_one[guild_id] = False
                repeat_embed.add_field(name="", value=f'''**"Repeat one"** has been **disabled**.''', inline=False)
        else:
            if repeat_all[guild_id] and option.value == "true":
                repeat_embed.add_field(name="", value=f'''**"Repeat all"** has been already **enabled**!''', inline=False)
            elif not repeat_all[guild_id] and option.value == "false":
                repeat_embed.add_field(name="", value=f'''**"Repeat all"** has been already **disabled**!''', inline=False)
            elif not repeat_all[guild_id] and option.value == "true":
                repeat_one[guild_id] = False
                repeat_all[guild_id] = True
                repeat_embed.add_field(name="", value=f'''**"Repeat all"** has been **enabled**.''', inline=False)
            elif repeat_all[guild_id] and option.value == "false":
                repeat_all[guild_id] = False
                repeat_embed.add_field(name="", value=f'''**"Repeat all"** has been **disabled**.''', inline=False)
        await interaction.response.send_message(embed=repeat_embed)

    # Replay the current track in the queue
    @app_commands.command(name="replay", description="Replay the current track from the beginning")
    async def replay(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        replay_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is None:
            replay_embed.add_field(name="", value="I'm not in a voice channel!", inline=False)
            return await interaction.response.send_message(embed=replay_embed)
        if not self.is_playing[guild_id]:
            replay_embed.add_field(name="", value="No tracks were playing in voice channel.", inline=False)
            return await interaction.response.send_message(embed=replay_embed)
        # Disable "repeat one" temporarily as it would affecting the entire process
        repeat_one_tmp = repeat_one[guild_id]
        repeat_one[guild_id] = False
        self.vc[guild_id].stop()
        current_track_queue_index[guild_id] -= 1
        if repeat_one_tmp:
            # Enable "repeat one" if it was enabled intentionally
            await asyncio.sleep(2)
            repeat_one[guild_id] = True
        replay_embed.add_field(name="", value=f"Replaying the current track...", inline=False)
        await interaction.response.send_message(embed=replay_embed)

    # Change the volume of the music player
    @app_commands.command(name="volume", description="Change the volume of the music player")
    @app_commands.describe(volume="The new volume you want me to set. Leave this blank if you want me to set it as default.")
    async def volume(self, interaction: Interaction, volume: Optional[app_commands.Range[int, 0, 200]] = 100):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        volume_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is None:
            volume_embed.add_field(name="", value="I'm not in a voice channel!", inline=False)
        elif self.vc[guild_id].source is None:
            self.player_volume[guild_id] = volume
            volume_embed.add_field(name="", value=f"Changed volume to **{volume}%**. The change will be effected when music starts to play.", inline=False)
        else:
            self.vc[guild_id].source.volume = volume / 100
            self.player_volume[guild_id] = volume
            volume_embed.add_field(name="", value=f"Changed volume to **{volume}%**", inline=False)
        await interaction.response.send_message(embed=volume_embed)

    # Show the volume of the music player
    @app_commands.command(name="showvolume", description="Show the volume of the music player")
    async def showvolume(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vc[guild_id] = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        volume_embed = discord.Embed(title="", color=interaction.user.colour)
        if self.vc[guild_id] is None:
            volume_embed.add_field(name="", value="I'm not in a voice channel!", inline=False)
        else:
            volume_embed.add_field(name="", value=f"Volume: **{self.player_volume[guild_id]}%**", inline=False)
        await interaction.response.send_message(embed=volume_embed)

    # Shows the queue
    @app_commands.command(name="queue", description="Shows the queue in this server")
    async def queue(self, interaction: Interaction):
        global selectlist
        guild_id = interaction.guild.id
        queue_embed = discord.Embed(title="Queue:", color=interaction.user.colour)
        if track_queue[guild_id] == []:
            # Returns nothing if the queue was empty
            queue_embed.add_field(name="", value="There are no tracks in the queue", inline=False)
            view = None
        elif current_track_queue_index[guild_id] == len(track_queue[guild_id]):
            # Returns nothing if the queue has been ended
            queue_embed.add_field(name=f"Now Playing :notes: :", value=f"There are no tracks playing now", inline=False)
            queue_embed.add_field(name="Upcoming Tracks:", value="There are no upcoming tracks will be played", inline=False)
            view = None
        elif current_track_queue_index[guild_id] + 1 == len(track_queue[guild_id]):
            # Return the track that currently playing if that track was the last track in the queue
            if track_queue[guild_id][current_track_queue_index[guild_id]][1] == "yt":
                # From YouTube
                queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['title']}", inline=False)
            else:
                # Custom file
                queue_embed.add_field(name="Now Playing :notes: :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['filename']}", inline=False)
            queue_embed.add_field(name="Upcoming Tracks:", value="There are no upcoming tracks will be played", inline=False)
            view = None
        else:
            # Refreshing page
            # 1st page
            total_page = math.ceil(float((len(track_queue[guild_id]) - current_track_queue_index[guild_id]) / tracks_per_page))
            start = current_track_queue_index[guild_id] + 1
            if len(track_queue[guild_id]) - current_track_queue_index[guild_id] - 1 > tracks_per_page:
                end = current_track_queue_index[guild_id] + 1 + tracks_per_page
            else:
                end = len(track_queue[guild_id])
            selectlist = []
            selectlist.append(discord.SelectOption(label=f"1", value=f"1", description=f"{start} - {end}"))
            if len(track_queue[guild_id]) - current_track_queue_index[guild_id] > tracks_per_page:
                for i in range(2, total_page + 1):
                    # 2nd page and so on
                    start = 1 + end
                    end = start + tracks_per_page
                    if start >= len(track_queue[guild_id]) + 1:
                        break
                    elif end >= len(track_queue[guild_id]):
                        if start > len(track_queue[guild_id]) - 1:
                            selectlist.append(discord.SelectOption(label=f"{i}", value=f"{i}", description=f"{len(track_queue[guild_id])}"))
                        else:
                            selectlist.append(discord.SelectOption(label=f"{i}", value=f"{i}", description=f"{start} - {len(track_queue[guild_id])}"))
                    else:
                        selectlist.append(discord.SelectOption(label=f"{i}", value=f"{i}", description=f"{start} - {end}"))
            # Retrieving tracks
            if len(track_queue[guild_id]) - current_track_queue_index[guild_id] - 1 > tracks_per_page:
                end = current_track_queue_index[guild_id] + 1 + tracks_per_page
            else:
                end = len(track_queue[guild_id])
            retval = ""
            for next_track_index in range(current_track_queue_index[guild_id] + 1, end):
                if track_queue[guild_id][next_track_index][1] == "yt":
                    # From YouTube
                    retval += f"**#{1 + next_track_index}** - " + track_queue[guild_id][next_track_index][0]['title'] + "\n"
                else:
                    # Custom file
                    retval += f"**#{1 + next_track_index}** - " + track_queue[guild_id][next_track_index][0]['filename'] + "\n"
            if retval != "":
                # Return the track that currently playing and all upcoming tracks normally
                if track_queue[guild_id][current_track_queue_index[guild_id]][1] == "yt":
                    # From YouTube
                    queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['title']}", inline=False)
                else:
                    # Custom file
                    queue_embed.add_field(name=f"Now Playing :notes: ({current_track_queue_index[guild_id] + 1}/{len(track_queue[guild_id])}) :", value=f"**#{current_track_queue_index[guild_id] + 1}** - {track_queue[guild_id][current_track_queue_index[guild_id]][0]['filename']}", inline=False)
                queue_embed.add_field(name="Upcoming Tracks:", value=retval, inline=False)
            view = DropdownView()
        if repeat_one[guild_id]:
            queue_embed.add_field(name='\u200b', value="", inline=False)
            queue_embed.add_field(name='''"Repeat one" has been enabled.''', value="", inline=False)
        if repeat_all[guild_id]:
            queue_embed.add_field(name='\u200b', value="", inline=False)
            queue_embed.add_field(name='''"Repeat all" has been enabled.''', value="", inline=False)
        if view is None:
            await interaction.response.send_message(embed=queue_embed)
        else:
            await interaction.response.send_message(embed=queue_embed, view=view)

    # Stops the track currently playing and clears the queue
    @app_commands.command(name="clear", description="Stops the track currently playing and clears the queue")
    async def clear(self, interaction: Interaction):
        guild_id = interaction.guild.id
        clear_embed = discord.Embed(title="Queue:", color=interaction.user.colour)
        if track_queue[guild_id] != []:
            track_queue[guild_id] = []
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
            current_track_queue_index[guild_id] == 0
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
        if track_queue[guild_id] != []:
            position = position or len(track_queue[guild_id])
            if position > len(track_queue[guild_id]):
                remove_embed.add_field(name="", value=f"Please enter a valid position of the track you want to remove from the queue.", inline=False)
            else:
                if position - 1 < 0:
                    track_queue[guild_id].pop(0)
                else:
                    track_queue[guild_id].pop(position - 1)
                remove_embed.add_field(name="", value=f"**#{position}** has been removed from queue.", inline=False)
            if (current_track_queue_index[guild_id] + 1) > position:
                current_track_queue_index[guild_id] -= 1
            guild_custom_dir = f"plugins/custom_audio/guild/{guild_id}"
            for track in track_queue[guild_id]:
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
                await interaction.response.send_message(f"I've joined the voice channel <#{voice_channel.id}>")
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
            await interaction.response.send_message(embed=AuthorNotInVoiceError(interaction, interaction.user).return_embed())

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
Just curious to know, where should I move them all into right now, <@{interaction.user.id}>？''')
        else:
            specified_vc = channel
        await interaction.response.send_message(f"Moving all users to <#{specified_vc.id}>...")
        # Return True when successful to move, or return False when no users were found in the voice channel.
        if await self.move_all_members(interaction, specified_vc, reason=reason):
            if reason is None:
                await interaction.edit_original_response(content=f"All users has been moved to <#{specified_vc.id}>.")
            else:
                await interaction.edit_original_response(content=f"All users has been moved to <#{specified_vc.id}> for **{reason}**.")
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
            return await interaction.response.send_message(f"<@{member.id}> currently not in a voice channel.")
        # Check the target vc
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move someone into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move <@{member.id}> into right now, <@{interaction.user.id}>？''')
        else:
            specified_vc = channel
        if reason is None:
            await member.move_to(specified_vc)
            if interaction.user.id == self.bot.application_id:
                return await interaction.response.send_message(f"I have been moved to <#{specified_vc.id}>. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.")
            await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}>.")
        else:
            await member.move_to(specified_vc, reason=reason)
            if interaction.user.id == self.bot.application_id:
                return await interaction.response.send_message(f"I have been moved to <#{specified_vc.id}> for **{reason}**. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.")
            await interaction.response.send_message(f"<@{member.id}> has been moved to <#{specified_vc.id}> for **{reason}**")

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
            await interaction.response.send_message(f"<@{interaction.user.id}> has been moved to <#{channel.id}>.")
        else:
            await interaction.user.move_to(channel, reason=reason)
            await interaction.response.send_message(f"<@{interaction.user.id}> has been moved to <#{channel.id}> for {reason}")

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
        # Getting bot member as a 'Member' object instead of 'ClientUser' object (which is why the bot.user is returning errors)
        guild = self.bot.get_guild(interaction.guild.id)
        bot_member = guild.get_member(self.bot.application_id)
        # Check the bot was in the vc or not
        if bot_member.voice is None:
            return await interaction.response.send_message(f"I'm currently not in a voice channel.")
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move me into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move into right now, <@{interaction.user.id}>？''')
        else:
            specified_vc = channel
        if reason is None:
            await bot_member.move_to(specified_vc)
            await interaction.response.send_message(f"I have been moved to <#{specified_vc.id}>.")
        else:
            await bot_member.move_to(specified_vc, reason=reason)
            await interaction.response.send_message(f"I have been moved to <#{specified_vc.id}> for **{reason}**.")

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
