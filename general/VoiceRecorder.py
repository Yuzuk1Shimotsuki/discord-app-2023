import discord
import os
import io
import time
import numpy as np
import wave
import wavelink
import tempfile
from discord import app_commands, Colour, Embed, Interaction
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink, VoiceData, WaveSink
from discord.ext.voice_recv.silence import SilenceGenerator
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Optional
from pydub import AudioSegment
from general.VoiceChannelFallbackConfig import *
from errorhandling.ErrorHandling import *

load_dotenv()

discord.opus._load_default()  # mandatory for those who wonder
record_path = f"configs/Bot/plugins/custom_recording/caches" # default record path


# ---------- <Voice Recorder>----------


def add_silence_to_wav(input_data: bytes, silence_duration: float) -> bytes:
    audio = AudioSegment.from_wav(io.BytesIO(input_data))
    silence = AudioSegment.silent(duration=int(silence_duration * 1000))  # pydub uses milliseconds
    final_audio = silence + audio
    output_buffer = io.BytesIO()
    final_audio.export(output_buffer, format="wav")
    return output_buffer.getvalue()


class MultiAudioImprovedWithSilenceSink(AudioSink):
    def __init__(self):
        super().__init__()
        self.user_sinks: Dict[int, WaveSink] = {}
        self.user_buffers: Dict[int, io.BytesIO] = {}
        self.silence_generators: Dict[int, SilenceGenerator] = {}
        self.start_time = time.perf_counter_ns()
        self.first_packet_time: Dict[int, int] = {}


    def _get_or_create_sink(self, user_id: int) -> WaveSink:
        if user_id not in self.user_sinks:
            buffer = io.BytesIO()
            sink = WaveSink(buffer)
            self.user_sinks[user_id] = sink
            self.user_buffers[user_id] = buffer
            self.silence_generators[user_id] = SilenceGenerator(sink.write)
            self.silence_generators[user_id].start()
        return self.user_sinks[user_id]


    def wants_opus(self) -> bool:
        return False


    def write(self, user: Optional[discord.User], data: VoiceData) -> None:
        if user is None:
            return

        sink = self._get_or_create_sink(user.id)
        silence_gen = self.silence_generators[user.id]
        
        if user.id not in self.first_packet_time:
            self.first_packet_time[user.id] = time.perf_counter_ns()

        silence_gen.push(user, data.packet)
        sink.write(user, data)


    def cleanup(self) -> None:
        for silence_gen in self.silence_generators.values():
            silence_gen.stop()
        self.user_sinks.clear()
        self.user_buffers.clear()
        self.silence_generators.clear()


    def get_user_audio(self, user_id: int) -> Optional[bytes]:
        if user_id in self.user_buffers:
            buffer = self.user_buffers[user_id]
            buffer.seek(0)
            audio_data = buffer.read()
            return audio_data
        
        return None


    def get_initial_silence_duration(self, user_id: int) -> float:
        if user_id in self.first_packet_time:
            return (self.first_packet_time[user_id] - self.start_time) / 1e9  # nano to sec
        
        return 0.0


    def mix_audio(self, audio_data_dict: Dict[int, bytes]) -> Optional[bytes]:
        audio_arrays = []
        sample_rate = 0
        num_channels = 0
        sample_width = 0

        for audio_data in audio_data_dict.values():
            if len(audio_data) <= 44:
                continue
            
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                params = wav_file.getparams()
                sample_rate = params.framerate
                num_channels = params.nchannels
                sample_width = params.sampwidth

                frames = wav_file.readframes(params.nframes)
                audio_array = np.frombuffer(frames, dtype=np.int16)
                audio_arrays.append(audio_array)

        if not audio_arrays:
            return None

        max_length = max(len(arr) for arr in audio_arrays)
        padded_audio_arrays = [np.pad(arr, (0, max_length - len(arr)), 'constant') for arr in audio_arrays]
        mixed_audio = np.mean(padded_audio_arrays, axis=0).astype(np.int16)

        output_buffer = io.BytesIO()
        with wave.open(output_buffer, 'wb') as output_wav:
            output_wav.setnchannels(num_channels)
            output_wav.setsampwidth(sample_width)
            output_wav.setframerate(sample_rate)
            output_wav.writeframes(mixed_audio.tobytes())
        
        output_buffer.seek(0)
        return output_buffer.read()


class VoiceRecorder(commands.Cog):
    global record_path

    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(record_path):
            os.makedirs(record_path)
        self.current_files = {}  # Dictionary to store files by user
        self.sinks = {}          # Dictionary to store sinks by user
        self.custom_sink = MultiAudioImprovedWithSilenceSink()
        self.is_recording = False


    # Starts the recording
    @app_commands.command(name="start-recording", description="🟢 Starts voice recording in the user's current voice channel")
    async def start_recording(self, interaction: Interaction):
        start_recording_success_embed = Embed(title="", color=interaction.user.color)
        start_recording_failure_embed = Embed(title="", color=Colour.red())
        if not interaction.user.voice:
            start_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> You must be connected to a voice channel to use this command.", inline=False)
            return await interaction.response.send_message(embed=start_recording_failure_embed, ephemeral=True)

        if self.bot.voice_clients:
            if isinstance(self.bot.voice_clients[0], wavelink.Player):
                start_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> The voice client is now being occupied by the music player, Please terminate the player and try again.", inline=False)
                return await interaction.response.send_message(embed=start_recording_failure_embed, ephemeral=True)
            
            else:
                start_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I'm already connected to a voice channel.", inline=False)
                return await interaction.response.send_message(embed=start_recording_failure_embed, ephemeral=True)

        voice_channel = interaction.user.voice.channel
        voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)

        if voice_client.is_listening():
            start_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Recording is already in progress.", inline=False)
            return await interaction.response.send_message(embed=start_recording_failure_embed, ephemeral=True)

        self.is_recording = True

        for member in voice_channel.members:
            if member.bot:
                continue

            voice_client.listen(self.custom_sink)

        start_recording_success_embed.add_field(name="", value=f":white_check_mark: :microphone2: Recording has **started**. Use **</stop-recording:1298511803277512806>** to **stop**.", inline=False)
        return await interaction.response.send_message(embed=start_recording_success_embed)


    # Stops the recording
    @app_commands.command(name="stop-recording", description="🔴 Stops the current voice recording")
    async def stop_recording(self, interaction: Interaction):
        voice_client = interaction.guild.voice_client
        stop_recording_success_embed = Embed(title="", color=interaction.user.color)
        stop_recording_failure_embed = Embed(title="", color=Colour.red())
        if not voice_client or not self.is_recording:
            stop_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> No recording in progress.", inline=False)
            return await interaction.response.send_message(embed=stop_recording_failure_embed, ephemeral=True)

        await interaction.response.defer()

        self.is_recording = False
        voice_client.stop_listening()
        all_audio_data = {}
        voice_channel = interaction.user.voice.channel

        # Collect audio data for each user
        for member in voice_channel.members:
            audio_data = self.custom_sink.get_user_audio(member.id)

            if audio_data and len(audio_data) > 44:  # Ensure the file isn't empty
                silence_duration = self.custom_sink.get_initial_silence_duration(member.id)
                final_audio_data = add_silence_to_wav(audio_data, silence_duration)
                all_audio_data[member.id] = final_audio_data

        if all_audio_data:
            # Mix all user audio data into one combined file
            combined_audio = self.custom_sink.mix_audio(all_audio_data)

            if combined_audio:
                # Use a temporary file to save the combined audio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(combined_audio)
                    temp_file_path = temp_file.name

                try:
                    # Send the combined audio file to the user
                    stop_recording_success_embed.add_field(name="", value=":white_check_mark: Recording finished.")
                    await interaction.followup.send(embed=stop_recording_success_embed, file=discord.File(temp_file_path, filename=f"combined_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"))

                except discord.errors.HTTPException as e:
                    if e.status == 413 and e.code == 40005:  # File too large
                        stop_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Failed to send the recording because the file was too large", inline=False)
                        return await interaction.followup.send(embed=stop_recording_failure_embed, ephemeral=True)
                    
                    else:
                        raise e

                finally:
                    # Ensure the temporary file is deleted
                    os.remove(temp_file_path)

        else:
            stop_recording_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Recording **failed** or the file is **empty**.", inline=False)
            return await interaction.followup.send(embed=stop_recording_failure_embed, ephemeral=True)
        

# ---------- </Voice Recorder>----------


async def setup(bot):
    await bot.add_cog(VoiceRecorder(bot))

