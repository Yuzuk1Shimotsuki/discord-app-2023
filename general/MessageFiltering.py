import discord
from discord.ext import commands


class MessageFiltering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_dm = False


  # ---------<Message Filtering>----------


    @commands.Cog.listener()
    async def on_message(self, message):
        
        # Check DM
        if isinstance(message.channel, discord.DMChannel):
            self.is_dm = True
        
        # Triggers and action
        if message.content.lower() == "hi":
            await message.channel.send("Hello!")
        
        # Deletes every single messages in guild system channel if it wasn't a sticker
        if self.is_dm and message.guild is None:
            return
        
        elif message.stickers == [] and message.channel == message.guild.system_channel:
            await message.delete()


  # ----------</Message Filtering>----------


async def setup(bot):
    await bot.add_cog(MessageFiltering(bot))
