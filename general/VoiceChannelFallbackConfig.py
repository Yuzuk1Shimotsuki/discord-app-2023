import discord
from discord import Interaction
from discord.ext import commands

fallback_text_channel = {}

def set_fallback_text_channel(interation: Interaction, channel: discord.TextChannel = None):
    if channel is not None:
        fallback_text_channel[interation.guild.id] = channel
        return fallback_text_channel[interation.guild.id]
    return None

# This is just a configuration for what to do when the application is disconnected from the client side. No commands.Cog are involved.
class VoiceChannelFallbackConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Nothing here

async def setup(bot):
    await bot.add_cog(VoiceChannelFallbackConfig(bot))