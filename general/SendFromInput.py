import discord
from discord import app_commands, Interaction
from discord.ext import commands
from typing import Optional


class SendFromInput(commands.Cog):
    def __init__(self, bot):
        global bool_value
        self.bot = bot


    # ----------<Send from input>----------


    # Send message from user input
    @app_commands.command(description="Send your message or attatchment")
    @app_commands.describe(silent="Send it as a silent message?")
    @app_commands.describe(message="The message u would like to send. Leave this empty if u want to send the attachment only.")
    @app_commands.describe(attachment="The attachment u would like to send. Leave this empty if u want to send the message only.")
    async def send(self, interaction: Interaction, silent: bool, message: Optional[str] = None, attachment: Optional[discord.Attachment] = None):

        if message is None and attachment is None:
            # Returns if no message or attachment are provided
            await interaction.response.send_message("You cannot let me to send nothing! (say at least send a message or an attachment)")

        else:
            # Sends the required input
            await interaction.response.defer()
            # Checks if the attachment is None or not

            if attachment is not None:
                # Converts the attachment to a discord.File() object
                files = await attachment.to_file()

                # Checks if the message is None or not
                if message is not None:
                    # Sends the message and the attachment in both
                    await interaction.channel.send(message, file=files, silent=silent)

                else:
                    # Sends the attachment only
                    await interaction.channel.send(file=files, silent=silent)

            else:
                # Sends the message only
                await interaction.channel.send(message, silent=silent)

            # Deletes the interaction
            msg = await interaction.followup.send('\u200b', silent=True)
            await msg.delete()

    # ----------</Send from input>----------

async def setup(bot):
    await bot.add_cog(SendFromInput(bot))
  