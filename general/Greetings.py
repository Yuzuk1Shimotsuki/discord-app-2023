import discord
from discord import app_commands, Interaction
from discord.ext import commands


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    # ----------<Greetings>----------

    # Greets the bot and recive a greeting message from the bot
    @app_commands.command(description="Greets the bot")
    async def hello(self, interaction: Interaction):
        await interaction.response.send_message(f"Hello! Nice to meet u!")

    # Greeting user when somebody joined
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Welcome message for new users DM 
        welcome_message_dm_user = f'''Hey <@!{member.id}>! Looks like u're the first time to join this server  :wave: 
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
        # Welcome message for the server system channel
        welcome_message_channel = f'Welcome <@!{member.id}>! Howdy?'
        # DM the user with welcome message when a new member joined the server and the member is not a bot.
        if not member.bot:
            await member.send(welcome_message_dm_user)
        # Send a welcome message to the system channel when a new user joined the server
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(welcome_message_channel)

    # ----------</Greetings>----------


async def setup(bot):
    await bot.add_cog(Greetings(bot))
