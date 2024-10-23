import discord
from discord import app_commands, Interaction
from discord.ext import commands
from errorhandling.ErrorHandling import *

# Main cog
class ReactingMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    reaction = app_commands.Group(name="reaction", description="Reacting to messages")

    # ----------<Reacting to messages>----------

    # Function of reacting to messages
    async def add_reaction(self, interaction, message, emoji):
        try:
            await message.add_reaction(emoji)
            return True
        except discord.HTTPException as error:
            if error.status == 400 and error.code == 10014:
                # An invaild emoji was given
                return await interaction.response.send_message(NotVaildEmojiError())
            else:
                raise error  # Raise other errors to ensure they aren't ignored
                
    # Function of remoing reactions for the bot
    async def remove_reaction(self, interaction, message, emoji):
        try:
            await message.remove_reaction(emoji, self.bot.user)
            return True
        except discord.HTTPException as error:
            if error.status == 400 and error.code == 10014:
                # An invaild emoji was given
                return await interaction.response.send_message(NotVaildEmojiError())
            else:
                raise error  # Raise other errors to ensure they aren't ignored

    # Getting required message ID from user input
    async def get_message_id(self, message: str):
        try:
            if message.startswith("https://discord.com/channels/"):
                # URL
                url_list = message.split("/")
                message_id = int(url_list[-1])
            else:
                # ID
                message_id = int(message)
            return message_id
        except ValueError:
            # The type of message user provided was not a valid type
            return None

    # Adding reaction to a specified message
    @reaction.command(name="add", description="Reacting to a specified message")
    @app_commands.describe(message="The ID of message (Enter the message ID e.g. 11xxx... or URL e.g. https://discord.com/channels/...)")
    @app_commands.describe(emoji="The emoji u want to reacts with")
    async def reaction_add(self, interaction: Interaction, message: str, emoji: str):
        message_id = await self.get_message_id(message)
        if message_id is None:
            # The type of message user provided was not a valid type
            return await interaction.response.send_message(InvaildTypeError())
        message = await interaction.channel.fetch_message(message_id)
        # Adding the reaction to the message
        if await self.add_reaction(interaction, message, emoji):
            await interaction.response.send_message(f"Reacted with {emoji} to the message.", ephemeral=True, silent=True, delete_after=1)

    # Removes the reaction performed by the bot from a specified message
    @reaction.command(name="remove", description="Removes the reaction performed by bot from a specified message")
    @app_commands.describe(message="The ID of message (Enter the message ID e.g. 11xxx... or URL e.g. https://discord.com/channels/...)")
    @app_commands.describe(emoji="The emoji u want to remove from the message")
    async def reaction_remove(self, interaction: Interaction, message: str, emoji: str):
        message_id = await self.get_message_id(message)
        if message_id is None:
            # The type of message user provided was not a valid type
            return await interaction.response.send_message(InvaildTypeError())
        message = await interaction.channel.fetch_message(message_id)
        # Removing the reaction from the message
        if await self.remove_reaction(interaction, message, emoji):
            await interaction.response.send_message(f"Removed the reaction {emoji} from the message.", ephemeral=True, silent=True, delete_after=1)

    # Listing all the reactions from a specified message
    @reaction.command(name="list", description="Listing all the reactions from a specified message")
    @app_commands.describe(message="The ID of message (Enter the message ID e.g. 11xxx... or URL e.g. https://discord.com/channels/...)")
    async def reaction_list(self, interaction: Interaction, message: str):
        message_id = await self.get_message_id(message)
        if message_id is None:
            # The type of message user provided was not a valid type
            return await interaction.response.send_message(InvaildTypeError())
        message = await interaction.channel.fetch_message(message_id)
        await interaction.response.defer()
        # Listing all the reactions from the message
        total_reactions = 0
        reactions = message.reactions
        if reactions == []:
            # Return the following message if there are no reactions
            await interaction.followup.send("No reactions were found in the message.")
        else:
            # Iterate through the reactions and add them to the embedded-message
            embed = discord.Embed(title="List of reactions from the message", color=interaction.user.colour)
            for reaction in reactions:
                embed.add_field(name=f"{reaction.emoji}：{reaction.count}", value="\u200b", inline=False)
                total_reactions += reaction.count
            embed.add_field(name=f"Number of total reactions: {total_reactions}", value="\u200b", inline=False)
            await interaction.followup.send(embed=embed)

    # Clearing all the reactions from a specified message
    @reaction.command(name="clear", description="Clear all reactions from a specified message")
    @app_commands.describe(message="The ID of message (Enter the message ID e.g. 11xxx... or URL e.g. https://discord.com/channels/...)")
    async def reaction_clear(self, interaction: Interaction, message: str):
        message_id = await self.get_message_id(message)
        if message_id is None:
            # The type of message user provided was not a valid type
            return await interaction.response.send_message(InvaildTypeError())
        message = await interaction.channel.fetch_message(message_id)
        await interaction.response.send_message("Clearing reactions...", ephemeral=True, silent=True, delete_after=0)
        # Clearing all the reactions from the message
        await message.clear_reactions()

    # Error handling
    async def cog_command_error(self, interaction: commands.Context, error: commands.CommandError):
        # Handles error for message could not be found
        if isinstance(error, commands.errors.MessageNotFound):
            await interaction.response.send_message(MessageNotFoundError())
        else:
            raise error  # Raise other errors to ensure they aren't ignored
    # ----------</Reacting to messages>----------
    

async def setup(bot):
    await bot.add_cog(ReactingMessages(bot))
