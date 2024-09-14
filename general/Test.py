
"""
MIT License

Copyright (c) 2019-Current PythonistaGuild, EvieePy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import logging
from typing import cast
import discord
from discord import app_commands, Interaction
from typing import Optional, List
from discord.ext import commands
import wavelink

class Test(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    discord.utils.setup_logging(level=logging.INFO)

    # Connect to lavalink node
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        nodes = [wavelink.Node(uri="http://linux20240907.eastus.cloudapp.azure.com:2333", password="youshallnotpass")]
        # cache_capacity is EXPERIMENTAL. Turn it off by passing None
        await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logging.info("Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed(title="Now Playing")
        embed.description = f"**{track.title}** by `{track.author}`"

        if track.artwork:
            embed.set_image(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`This track was recommended via {track.source}`"

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)
        
        await player.channel.send(embed=embed)


    @commands.command()
    async def play1(self, ctx: commands.Context, *, query: str) -> None:
        """Play a song with the given query."""
        if not ctx.guild:
            return

        player: wavelink.Player
        player = cast(wavelink.Player, ctx.voice_client)  # type: ignore

        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)  # type: ignore
            except AttributeError:
                await ctx.send("Please join a voice channel first before using this command.")
                return
            except discord.ClientException:
                await ctx.send("I was unable to join this voice channel. Please try again.")
                return

        # Turn on AutoPlay to enabled mode.
        # enabled = AutoPlay will play songs for us and fetch recommendations...
        # partial = AutoPlay will play songs for us, but WILL NOT fetch recommendations...
        # disabled = AutoPlay will do nothing...
        #player.autoplay = wavelink.AutoPlayMode.enabled
        player.autoplay = wavelink.AutoPlayMode.partial

        """"
        # Lock the player to this channel...
        if not hasattr(player, "home"):
            player.home = ctx.channel
        elif player.home != ctx.channel:
            await ctx.send(f"You can only play songs in {player.home.mention}, as the player has already started there.")
            return
        """

        # This will handle fetching Tracks and Playlists...
        # Seed the doc strings for more information on this method...
        # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
        # Defaults to YouTube for non URL based queries...
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            await ctx.send(f"{ctx.author.mention} - Could not find any tracks with that query. Please try again.")
            return

        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await player.queue.put_wait(tracks)
            await ctx.send(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await ctx.send(f"Added **`{track}`** to the queue.")

        if not player.playing:
            # Play now since we aren't playing anything...
            await player.play(player.queue.get(), volume=30)

        # Optionally delete the invokers message...
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass

    # Pauses the current track
    @app_commands.command(name="pause", description="Pauses the current track being played in voice channel")
    async def pause(self, interaction: Interaction):
        pause_embed = discord.Embed(title="", color=interaction.user.colour)
        if interaction.guild.voice_client is None:
            pause_embed.add_field(name="", value="No tracks were playing. I'm not even in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=pause_embed)
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        if player is not None:
            if player.paused:
                pause_embed.add_field(name="", value="The track has been already paused!", inline=False)
            else:
                await player.pause(True)
                pause_embed.add_field(name="", value="The track has been paused.", inline=False)
        else:
            pause_embed.add_field(name="", value="No tracks were playing in voice channel.", inline=False)
        await interaction.response.send_message(embed=pause_embed)

    # Resume a paused track
    @app_commands.command(name = "resume", description="Resume a paused track in voice channel")
    async def resume(self, interaction: Interaction):
        guild_id = interaction.guild.id
        resume_embed = discord.Embed(title="", color=interaction.user.colour)
        if interaction.guild.voice_client is None:
            resume_embed.add_field(name="", value="No track has been paused before. I'm not even in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=resume_embed)
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        if player is not None:
            if not player.paused:
                resume_embed.add_field(name="", value="No track has been paused before in voice channel.", inline=False)
            else:
                await player.pause(False)
                resume_embed.add_field(name="", value="Resuming the track...", inline=False)
        else:
            resume_embed.add_field(name="", value="No track has been paused before in voice channel.", inline=False)
        await interaction.response.send_message(embed=resume_embed)

    # Replay the current track in the queue
    @app_commands.command(name="replay", description="Replay the current track from the beginning")
    async def replay(self, interaction: Interaction):
        guild_id = interaction.guild.id
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        replay_embed = discord.Embed(title="", color=interaction.user.colour)
        if player is None:
            replay_embed.add_field(name="", value="I'm not in a voice channel!", inline=False)
            return await interaction.response.send_message(embed=replay_embed)
        if player.paused or not player.playing:
            replay_embed.add_field(name="", value="No tracks were playing in voice channel.", inline=False)
            return await interaction.response.send_message(embed=replay_embed)
        await player.seek(0)   # To restart the song from the beginning, disregard this parameter or set position to 0.
        replay_embed.add_field(name="", value=f"Replaying the current track...", inline=False)
        await interaction.response.send_message(embed=replay_embed)

    # Plays the previous track in history
    @app_commands.command(name="previous", description="Plays the previous track in history")
    async def previous(self, interaction: Interaction):
        player = cast(wavelink.Player, interaction.guild.voice_client)
        prev_embed = discord.Embed(title="", color=interaction.user.colour)
        if player is None:
            prev_embed.add_field(name="", value="There is no previous track in history. I'm not even in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=prev_embed)
        elif player and len(player.queue.history) == 0:
            prev_embed.add_field(name="", value="There is no previous track in history.", inline=False)
        else:
            prev_track = player.queue.history[-2]  # Get the last song in the history
            await player.play(prev_track)
            prev_embed.add_field(name="", value="Playing previous track in history...", inline=False)
        await interaction.response.send_message(embed=prev_embed)


    @commands.command()
    async def nightcore(self, ctx: commands.Context) -> None:
        """Set the filter to a nightcore style."""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            return

        filters: wavelink.Filters = player.filters
        filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
        await player.set_filters(filters)

        await ctx.message.add_reaction("\u2705")

    @commands.command()
    async def volume(self, ctx: commands.Context, value: int) -> None:
        """Change the volume of the player."""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            return

        await player.set_volume(value)
        await ctx.message.add_reaction("\u2705")


    @commands.command(aliases=["dc"])
    async def disconnect(self, ctx: commands.Context) -> None:
        """Disconnect the Player."""
        player: wavelink.Player = cast(wavelink.Player, ctx.voice_client)
        if not player:
            return

        await player.disconnect()
        await ctx.message.add_reaction("\u2705")


    # Discord Autocomplete for YouTube search, rewrited for discord.py
    async def web_serach_autocomplete(self,
        interaction: Interaction,
        query: str
    ) -> List[app_commands.Choice[str]]:
        if interaction.namespace.source == "web":
            result_list = []
            if not query.startswith("https://"):
                # Serach from keywords
                try:
                    max_limit = 25
                    search: wavelink.Search = await wavelink.Playable.search(query)
                    for i in range(max_limit):
                        try:
                            result_list.append(search[i].title)
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
    @app_commands.choices(source=[app_commands.Choice(name="Web", value="web"),
                                    app_commands.Choice(name="Custom files", value="custom")
                                    ])
    @app_commands.autocomplete(query=web_serach_autocomplete)
    async def play(self, interaction:Interaction, source: app_commands.Choice[str], query: Optional[str] = None, attachment: Optional[discord.Attachment] = None):
        guild_id = interaction.guild.id
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)  # type: ignore
            except AttributeError:
                await interaction.response.send_message("Please join a voice channel first before using this command.")
                return
            except discord.ClientException:
                await interaction.response.send_message("I was unable to join this voice channel. Please try again.")
                return
        # Turn on AutoPlay to enabled mode.
        # enabled = AutoPlay will play songs for us and fetch recommendations...
        # partial = AutoPlay will play songs for us, but WILL NOT fetch recommendations...
        # disabled = AutoPlay will do nothing...
        player.autoplay = wavelink.AutoPlayMode.partial

        # Lock the player to this channel...
        if not hasattr(player, "home"):
            player.home = interaction.channel
        elif player.home != interaction.channel:
            await interaction.response.send_message(f"You can only play songs in {player.home.mention}, as the player has already started there.")
            return
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            await interaction.response.send_message(f"{interaction.user.mention} - Could not find any tracks with that query. Please try again.")
            return
        
        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            added: int = await player.queue.put_wait(tracks)
            await interaction.response.send_message(f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await interaction.response.send_message(f"Added **`{track}`** to the queue.")

        if not player.playing:
            # Play now since we aren't playing anything...
            await player.play(player.queue.get(), volume=30)

    # Skipping tracks
    @app_commands.command(name="skip", description="Skips the current track being played in voice channel")
    @app_commands.describe(amount="Number of track to skip. Leave this blank if you want to skip the current track only.")
    async def skip(self, interaction: Interaction, amount: Optional[app_commands.Range[int, 1]] = 1):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        skip_embed = discord.Embed(title="", color=interaction.user.colour)
        if player is None:
            skip_embed.add_field(name="", value="I'm not in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=skip_embed)
        if player.current and player.queue.is_empty:
            await player.skip(force=True)
            # The author just skipped the final track
            skip_embed.add_field(name="", value=f'''Skipped the final track. There are no upcoming tracks will be played unless **"Repeat all"** was **enabled**.''', inline=False)
        elif amount > player.queue.count:
            skip_embed.add_field(name="", value="The amount of tracks you tried to skip exceeded the total number of available tracks can be skipped in the queue. Automatically skipping to the last track in the queue...", inline=False)
            await player.play(track=player.queue[-1])
        else:
            # Skip one or multiple tracks
            current_playing = None
            current_playing == player.current
            count = amount
            while count > 0:
                track = await player.skip(force=True)
                if track != current_playing:
                    break
                count -= 1
            if amount > 1:
                skip_embed.add_field(name="", value=f"Skipped **{amount}** tracks in the queue", inline=False)
            else:
                skip_embed.add_field(name="", value="Skipped the current track", inline=False)
        await interaction.response.send_message(embed=skip_embed)

    # Shows the queue
    @app_commands.command(name="queue", description="Shows the queue in this server")
    async def queue(self, interaction: Interaction):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)  # type: ignore
        queue_embed = discord.Embed(title="Queue:", color=interaction.user.colour)
        if player is None:
            queue_embed.add_field(name="", value="Please invite me to a voice channel first before using this command.")
            return await interaction.response.send_message(embed=queue_embed)
        if player.current is None and player.queue.is_empty:
            queue_embed.add_field(name="", value="There are no tracks in the queue", inline=False)
        if player.current is None:
            queue_embed.add_field(name=f"Now Playing :notes: :", value=f"There are no tracks playing now", inline=False)
        else:
            queue_embed.add_field(name=f"Now Playing :notes: :", value=f"> {player.current.title}", inline=False)
            if player.queue.is_empty:
                queue_embed.add_field(name="Upcoming Tracks:", value="There are no upcoming tracks will be played", inline=False)
            else:
                for item in player.queue:
                    queue_embed.add_field(name="Upcoming Tracks:", value=f"> {item.title}", inline=False)
        await interaction.response.send_message(embed=queue_embed)
        
        


        print(player.current)
        print(player.queue)

        """"
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
        """


async def setup(bot):
    await bot.add_cog(Test(bot))


