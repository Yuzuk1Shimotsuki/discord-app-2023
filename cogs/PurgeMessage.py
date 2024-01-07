import discord
from discord import Interaction, Option
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class PurgeMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Purge>----------

    # Purge messages
    @commands.slash_command(name="purge", description="Delete messages from the present text channel. This command does not deletes pinned messages.")
    @commands.has_permissions(administrator=True)
    async def purge(self, interaction: Interaction, amount: Option(int, min_value=1, description="Number of messages to purge", required=True)):
        await interaction.defer(ephemeral=True)
        def not_pinned(msg):
            return not msg.pinned
        if amount == 1:
            purgeEmbed = discord.Embed(title="Message Purge", description="You have successfully purged 1 message.", color=0x00ff00)
            await interaction.channel.purge(limit=amount, check=not_pinned)
        elif amount > 1:
            purgeEmbed = discord.Embed(title="Message Purge", description=f"You have successfully purged {amount} messages.", color=0x00ff00)
            await interaction.channel.purge(limit=amount, check=not_pinned)
        purgeEmbed.set_image(url="https://media.discordapp.net/attachments/737732516588290110/1084510457387307048/presto-purge.png")
        await interaction.followup.send(embed=purgeEmbed, ephemeral=True, delete_after=2)

    @purge.error
    async def purge_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to purge messages!")
        else:
            raise error

# ----------</Purge>----------


def setup(bot):
    bot.add_cog(PurgeMessage(bot))
