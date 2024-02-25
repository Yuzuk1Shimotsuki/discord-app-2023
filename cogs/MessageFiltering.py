import discord
from discord.ext import commands


class MessageFiltering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

  # ---------<Message Filtering>----------

    @commands.Cog.listener()
    async def on_message(self, message):
        # 
        # Triggers and action
        # 
        if message.content.lower() == "hi":
            await message.channel.send("Hello!")

  # ----------</Message Filtering>----------


async def setup(bot):
    await bot.add_cog(MessageFiltering(bot))
  