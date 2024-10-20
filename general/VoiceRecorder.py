import discord
import os
import io
import time
import numpy as np
import wave
from discord import app_commands, Interaction
from discord.ext import voice_recv
from discord.ext.voice_recv import AudioSink, VoiceData, WaveSink
from discord.ext.voice_recv.silence import SilenceGenerator
from datetime import datetime
from typing import Dict, Optional
from pydub import AudioSegment
from general.VoiceChannelFallbackConfig import *
from errorhandling.ErrorHandling import *

discord.opus._load_default()  # mandatory for those who wonder
record_path = f"plugins/custom_recording/caches" # default record path

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
    record = app_commands.Group(name="record", description="Recording in voice channels commands")

    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(record_path):
            os.makedirs(record_path)
        self.current_files = {}  # Dictionary to store files by user
        self.sinks = {}          # Dictionary to store sinks by user
        self.custom_sink = MultiAudioImprovedWithSilenceSink()
        self.is_recording = False

    @record.command(name="start", description="🟢 Starts voice recording in the user's current voice channel")
    async def voice_start(self, interaction: Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message("<a:CrossRed:1274034371724312646> You must be connected to a voice channel to use this command.", ephemeral=True)

        if self.bot.voice_clients:
            return await interaction.response.send_message("<a:CrossRed:1274034371724312646> I'm already connected to a voice channel.", ephemeral=True)

        voice_channel = interaction.user.voice.channel
        voice_client = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)

        if voice_client.is_listening():
            return await interaction.response.send_message("<a:CrossRed:1274034371724312646> Recording is already in progress.", ephemeral=True)

        self.is_recording = True

        for member in voice_channel.members:
            if member.bot:
                continue
            voice_client.listen(self.custom_sink)

        await interaction.response.send_message("🎙️ Recording has started. Use /var end to finish.")

    @record.command(name="end", description="🔴 Stops the current voice recording")
    async def voice_end(self, interaction: Interaction):
        voice_client = interaction.guild.voice_client
        if not voice_client or not self.is_recording:
            return await interaction.response.send_message("<a:CrossRed:1274034371724312646> No recording in progress.", ephemeral=True)

        await interaction.response.defer()

        self.is_recording = False
        record_result_embed = discord.Embed(title="", description="", timestamp=datetime.now(), color=interaction.user.colour)
        voice_client.stop_listening()
        all_audio_data = {}
        voice_channel = interaction.user.voice.channel
        for member in voice_channel.members:
            
            audio_data = self.custom_sink.get_user_audio(member.id)
            if audio_data and len(audio_data) > 44:
                silence_duration = self.custom_sink.get_initial_silence_duration(member.id)
                final_audio_data = add_silence_to_wav(audio_data, silence_duration)
                all_audio_data[member.id] = final_audio_data
        
        if all_audio_data:
            combined_audio = self.custom_sink.mix_audio(all_audio_data)
            if combined_audio:
                combined_file_path = f"{record_path}/combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                
                with open(combined_file_path, 'wb') as f:
                    f.write(combined_audio)
                    try:
                        await interaction.followup.send(
                            "✅ Recording finished.",
                            file=discord.File(combined_file_path)
                        )
                    except discord.errors.HTTPException as e:
                        if e.status == 413 and e.code == 40005:
                            return await interaction.followup.send("<a:CrossRed:1274034371724312646> Failed to send the recording because the file was too large")
                        else:
                            raise e
        else:
            record_result_embed.add_field(name="", value="<a:CrossRed:1274034371724312646> Recording **failed** or the file is **empty**.", inline=False)
            return await interaction.followup.send(embed=record_result_embed)

# ---------- </Voice Recorder>----------

async def setup(bot):
    await bot.add_cog(VoiceRecorder(bot))



