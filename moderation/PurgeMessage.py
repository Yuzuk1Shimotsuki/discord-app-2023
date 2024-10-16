import discord
import asyncio
from discord import app_commands, Interaction
from discord.ext import commands
from discord.app_commands.errors import MissingPermissions
from typing import Optional


class PurgeMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Purge>----------

    # Purge messages
    @app_commands.command(name="purge", description="Delete messages from the present text channel. This command does not deletes pinned messages.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(amount="Number of messages to purge")
    async def purge(self, interaction: Interaction, amount: Optional[app_commands.Range[int, 1]] = 1):
        await interaction.response.defer(ephemeral=True)
        def not_pinned(msg):
            return not msg.pinned
        if amount == 1:
            purgeEmbed = discord.Embed(title="Message Purge", description="You have successfully purged 1 message.", color=0x00ff00)
            await interaction.channel.purge(limit=amount, check=not_pinned)
        elif amount > 1:
            purgeEmbed = discord.Embed(title="Message Purge", description=f"You have successfully purged {amount} messages.", color=0x00ff00)
            await interaction.channel.purge(limit=amount, check=not_pinned)
        purgeEmbed.set_image(url="https://media.discordapp.net/attachments/737732516588290110/1084510457387307048/presto-purge.png")
        msg = await interaction.followup.send(embed=purgeEmbed, ephemeral=True, silent=True)
        await asyncio.sleep(1.5)
        await msg.delete()

    @purge.error
    async def purge_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to purge messages!")
        else:
            raise error

# ----------</Purge>----------


async def setup(bot):
    await bot.add_cog(PurgeMessage(bot))
