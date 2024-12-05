import discord
from discord import app_commands, Colour, Interaction, Embed, Message
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class MessageFiltering(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_sysdel = False    # Default
        self.db = self.bot.get_cluster()


  # ---------<Message Filtering>----------


    # Toggle the option of deleting messages from the system channel
    @app_commands.command(name="sysdel", description="Configure the option of deleting messages from the system channel")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(mode="Enable or disable?")
    async def sysdel(self, interaction: Interaction, mode: bool):
        sysdel_success_embed = Embed(title="", color=interaction.user.color)
        sysdel_failure_embed = Embed(title="", color=Colour.red())

        # Access database
        database = self.db.preferences
        delete_on_system_channel_collection = database["delete_on_system_channel"]

        # Check if the guild already has a setting for `delete_on_system_channel`
        existing_setting = delete_on_system_channel_collection.find_one({"id": interaction.guild.id})

        if existing_setting:
            # Check if the current mode is the same as the requested mode
            if existing_setting.get("delete_on_system_channel") == mode:
                current_status = "enabled" if mode else "disabled"
                sysdel_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> The **delete on system channel** option is already **{current_status}** for this server.")
                return await interaction.response.send_message(embed=sysdel_failure_embed, ephemeral=True)
            
            else:
                # Update the setting since the requested mode is different
                delete_on_system_channel_collection.update_one(
                    {"id": interaction.guild.id}, 
                    {"$set": {"delete_on_system_channel": mode}}
                )
        
        else:
            # Insert a new document if it doesn't already exist
            delete_on_system_channel_collection.insert_one({"id": interaction.guild.id, "delete_on_system_channel": mode})

        # Respond with the updated status
        updated_status = "enabled" if mode else "disabled"
        sysdel_success_embed.add_field(name="", value=f"The **delete on system channel** option has been **{updated_status}** for this server.")
        await interaction.response.send_message(embed=sysdel_success_embed, ephemeral=True)

    
    @sysdel.error
    async def sysdel_error(self, interaction: Interaction, error):
        sysdel_error_embed = Embed(title="", color=discord.Colour.red())
        
        if isinstance(error, MissingPermissions):
            sysdel_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `Manage Server` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=sysdel_error_embed)
        else:
            raise error


    @commands.Cog.listener()
    async def on_message(self, message: Message):

        # Access database
        database = self.db.preferences
        delete_on_system_channel_collection = database["delete_on_system_channel"]

        # Triggers and action for all channels
        if message.content.lower() == "hi":
            await message.channel.send("Hello!")

        # Ensure:
        # - this is a system channel in a guild
        # Actions:
        # - Deletes every single messages in the system channel if it wasn't a sticker

        if isinstance(message.channel, discord.DMChannel) or message.guild is None:    # If this was true this could be a DM or ephemeral message
            return

        # Check if the guild already has a setting for `delete_on_system_channel`
        existing_setting = delete_on_system_channel_collection.find_one({"id": message.guild.id})

        if existing_setting:
            self.is_sysdel = existing_setting.get("delete_on_system_channel")    # Get current mode for the guild
        
        if self.is_sysdel and message.stickers == [] and message.channel == message.guild.system_channel:
            await message.delete()


  # ----------</Message Filtering>----------


async def setup(bot):
    await bot.add_cog(MessageFiltering(bot))


