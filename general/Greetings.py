import discord
from discord import app_commands, Interaction, Embed, TextStyle, Member
from discord.ui import Modal, TextInput
from discord.ext import commands
from discord.ext.commands import MissingPermissions


# Formater for custom welcome messages (DO NOT MODIFY THE VALUES UNLESS YOU KNOW WHAT YOU'RE DOING)
def welcome_formater(message: str, member: Member):
    formats = {
        "{user}": member.mention,
        "{user.mention}": member.mention,
        "{member}": member.mention,
        "{member.mention}": member.mention,
        "{server}": member.guild.name,
        "{server.name}": member.guild.name,
        "{guild}": member.guild.name,
        "{guild.name}": member.guild.name,
        "{user.avatar}": member.display_avatar.url,
        "{user.display_avatar}": member.display_avatar.url,
        "{member.avatar}": member.display_avatar.url,
        "{member.display_avatar}": member.display_avatar.url
    }

    for key, value in formats.items():
        message = message.replace(key, value)
    return message

class CustomWelcomeMessage(Modal):
    def __init__(self, db):
        self.db = db    # Connect to MongoDB
        super().__init__(title="Configure your own welcome message")

    dm_welcome_message = TextInput(
        label="DM message",
        placeholder="Your content here...\n(Note: Use {member} for mention)",
        style=TextStyle.paragraph,
        max_length=4000,
        required=False
    )
    server_welcome_message = TextInput(
        label="Server message",
        placeholder="Your content here...\n(Note: Use {member} for mention)",
        style=TextStyle.paragraph,
        max_length=4000,
        required=False
)

    async def on_submit(self, interaction: Interaction):
        update_success_embed = Embed(title="Success", color=interaction.user.color)
        update_failure_embed = Embed(title="Error", color=discord.Color.red())        

        # Store to the database
        database = self.db["welcome_message"]
        dm_welcome_message_collections = database["dm"]
        server_welcome_message_collections = database["guild"]
        try:
            update_dm = False
            update_server = False

            # Update the message if find any or create one to the database
            if self.dm_welcome_message.value != "":
                if await dm_welcome_message_collections.find_one_and_update({"id": interaction.guild.id}, {"$set": { "message": self.dm_welcome_message.value }}, new=True) is None:  # Update the message
                    await dm_welcome_message_collections.insert_one({"id": interaction.guild.id, 'message': self.dm_welcome_message.value})
                update_dm = True
            
            if self.server_welcome_message.value != "":
                if await server_welcome_message_collections.find_one_and_update({"id": interaction.guild.id}, {"$set": { "message": self.server_welcome_message.value }}, new=True) is None:  # Update the message
                    await server_welcome_message_collections.insert_one({"id": interaction.guild.id, 'message': self.server_welcome_message.value})
                update_server = True
            
            if update_dm or update_server:
                update_success_embed.add_field(name="", value=f"The **welcome message** for {"**DM**" if update_dm else "**system channel**"} has been **updated** for this server.")
            
            else:
                update_success_embed.add_field(name="", value=f"Both **welcome messages** for **DM** and **system channel** has been **updated** for this server.")
            
            await interaction.response.send_message(embed=update_success_embed)

        except Exception as e:
            update_failure_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> An error occured while updating the welcome messages.\nDetails: {e}")
            await interaction.response.send_message(embed=update_failure_embed)
            

class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.db = self.bot.get_cluster()


    # ----------<Greetings>----------


    # Configure or update the welcome message for the server
    @app_commands.command(description="Configure or update the welcome message for the server")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome(self, interaction: Interaction):
        await interaction.response.send_modal(CustomWelcomeMessage(db=self.db))


    @welcome.error
    async def welcome_error(self, interaction: Interaction, error):
        welcome_error_embed = Embed(title="", color=discord.Colour.red())
        
        if isinstance(error, MissingPermissions):
            welcome_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `Manage Server` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=welcome_error_embed)
        else:
            raise error
        

    # Greets the bot and recive a greeting message from the bot
    @app_commands.command(description="Greets the bot")
    async def hello(self, interaction: Interaction):
        await interaction.response.send_message(f"Hi! Nice to meet you :)")


    # Greeting user when somebody joined
    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        # Default welcome message for new users DM 
        default_dm_welcome_message = f'''Hey {member.mention} Looks like u're the first time to join this server  :wave: 
First of all, welcome and thanks for joining!

Next, our server contains a couple of rules. Please read them in advance before sending ur first message.

# **:tools:  General Rules**
1. **Be respectful** - You must respect all users, especially moderators. Regardless of your liking towards them, treat others the way you want to be treated.

2. **No Inappropriate Language** - The use of profanity should be kept to a minimum. ~~However, any derogatory language towards any user is prohibited.~~

(Although this action is not completely prohibited from our server, it's recommended to behave urself in advance when speaking for good habits)

# **3. No spamming - Don't send a lot of small messages right after each other. Do not disrupt chat by spamming. **
# **(This is VERY IMPORTANT, due to my old pc f*cked up by 1000+msg/min. Affenders could be banned from all text and voice channels for 2 weeks)**
_ _
~~4. **No pornographic/adult/other NSFW material** - This is a community server and not meant to share this kind of material.~~ 
(Idc about this one but... please don't sent it frequently)

~~5. **No advertisements** - We do not tolerate any kind of advertisements, whether it be for other communities or streams. You can post your content in the media channel if it is relevant and provides actual value (Video/Art)~~ 
(Whatever u decide it)

~~6. **No offensive names and profile pictures** - You will be asked to change your name or picture if the staff deems them inappropriate.~~ 
(Just fine who cares lol)

7. Follow the **Discord Community Guidelines** - You can find them here: https://discordapp.com/guidelines

And finally, have fun and enjoy in our server!

Regards,
The administration team of this server
'''     
        # Default welcome message from the system channel in server
        default_server_welcome_message = f'Welcome {member.mention}! Howdy?'

        # Check if the custom message exsist on the mongo database or not
        database = self.db["welcome_message"]
        dm_welcome_message_collections = database["dm"]
        server_welcome_message_collections = database["guild"]
        
        # Return the message as a dictionary (if any)
        dm_welcome_message = await dm_welcome_message_collections.find_one({"id": member.guild.id})
        server_welcome_message = await server_welcome_message_collections.find_one({"id": member.guild.id})

        # Set the welcome messages from database or use the default message
        dm_welcome_message = welcome_formater(dm_welcome_message["message"], member) if dm_welcome_message else default_dm_welcome_message
        server_welcome_message = welcome_formater(server_welcome_message["message"], member) if server_welcome_message else default_server_welcome_message

        # DM the user with welcome message when a new member joined the server and the member is not a bot.
        if not member.bot:
            await member.send(dm_welcome_message)
        
        # Send a welcome message to the system channel when a new user joined the server
        channel = member.guild.system_channel
        
        if channel is not None:
            await channel.send(server_welcome_message)


    # ----------</Greetings>----------


async def setup(bot):
    await bot.add_cog(Greetings(bot))

