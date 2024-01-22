import discord
from discord import SlashCommandGroup, Interaction, Option
from discord.ext import commands
from discord.utils import get
from datetime import datetime

poll_mode = ["Options", "Like/Dislike"]
poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "👍", "👎"]


class ResetConfirm(discord.ui.View):
    # "Yes" button
    @discord.ui.button(label="Yes", row=0, custom_id="yes_button01", style=discord.ButtonStyle.danger)
    async def first_button_callback(self, button, interaction):
        await interaction.response.edit_message(content="The poll has been reset.", view=None)

    # "No" button
    @discord.ui.button(label="No", row=0, custom_id="no_button02", style=discord.ButtonStyle.secondary)
    async def second_button_callback(self, button, interaction):
        await interaction.response.edit_message(content="The reset was aborted.", view=None)


class Poll(commands.Cog):
    def __init__(self, bot):
        global poll_emojis
        global poll_mode
        self.bot = bot
        self.poll_message = {}
        self.poll_options = {}
        self.poll_reactions = {}
        self.poll_count = {}
        self.poll_type = {}
        self.total_members = {}
        self.poll_members = {}
        self.total_votes = {}
        self.reaction_rate = {}
        self.reset_confirm_message = {}
        self.reset_confirm_option = {}


    poll = SlashCommandGroup("poll", "Poll commands")

    # ----------<Poll>----------

    # Startup
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            guild_id = int(guild.id)
            self.poll_message[guild_id] = None
            self.poll_options[guild_id] = None
            self.poll_reactions[guild_id] = []
            self.poll_count[guild_id] = {}
            self.poll_type[guild_id] = None
            self.total_members[guild_id] = []
            self.poll_members[guild_id] = []
            self.total_votes[guild_id] = 0
            self.reaction_rate[guild_id] = 0
            self.reset_confirm_message[guild_id] = None
            self.reset_confirm_option[guild_id] = None

    # Function of resetting a poll
    async def reset(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.poll_message[guild_id] = None
        self.poll_options[guild_id] = None
        self.poll_reactions[guild_id] = []
        self.poll_count[guild_id] = {}
        self.poll_type[guild_id] = None
        self.total_members[guild_id] = []
        self.poll_members[guild_id] = []
        self.total_votes[guild_id] = 0
        self.reaction_rate[guild_id] = 0
        self.reset_confirm_message[guild_id] = None
        self.reset_confirm_option[guild_id] = None

    # Confirming reset
    async def poll_reset_confirm_msg(self, interaction: Interaction, message: str):
        guild_id = interaction.guild.id
        if message is None:
            message = "Are you sure you want to reset the poll?"
        await interaction.response.defer()
        # Displaying confirm buttons from event reset()
        view = ResetConfirm()
        self.reset_confirm_message[guild_id] = await interaction.followup.send(message, view=view)
        res = await self.bot.wait_for('interaction', check=lambda interaction: interaction.data["component_type"] == 2 and "custom_id" in interaction.data.keys())
        # Loop through the children of the view and get the button with corresponding custom_id
        for item in view.children:
            if item.custom_id == res.data["custom_id"]:
                button = item
        # Execute the commamd for the selected button
        if button.custom_id == "yes_button01":
            await self.reset(interaction)
        else: # "no_button02"
            channel = self.bot.get_channel(self.reset_confirm_message[guild_id].channel.id)
            msg_to_delete = await channel.fetch_message(self.reset_confirm_message[guild_id].id)
            await msg_to_delete.delete()
        # Return selected button for futher purpose
        self.reset_confirm_option[guild_id] = button.custom_id

    # Reset the poll
    @poll.command(name="reset", description="Reset the poll")
    async def poll_reset(self, interaction: Interaction):
        if self.poll_message is not None:
            await self.poll_reset_confirm_msg(interaction, None)
        else:
            await interaction.response.send_message("There is currently no poll needs to reset.", ephemeral=True)

    # Fetching the amount 
    async def fetch_poll_count(self, guild_id):
        for emojis in poll_emojis:
            cache_message = get(self.bot.cached_messages, id=self.poll_message[guild_id].id)
            reaction = get(cache_message.reactions, emoji=emojis)
            try:
                self.poll_count[guild_id][f"{emojis}"] = reaction.count - 1
                print(self.poll_count[guild_id])
            except AttributeError:
                pass

    # Appends a member to the list when someone reacts the message, with conditions
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = payload.guild_id
        # Checks threre is a poll message or not, if yes, proceed
        if self.poll_message[guild_id] is not None:
            # Checks the payload message is equals to the poll message or not, if yes, proceed
            if payload.message_id == self.poll_message[guild_id].id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                # Checks the member is a bot or not
                if member.bot:
                    return
                if member in self.poll_members[guild_id]:
                    # This member is already in the list
                    # Remove the lastest reaction done by the member
                    self.poll_members[guild_id].append(member)
                    await self.poll_message[guild_id].remove_reaction(payload.emoji, member)
                elif str(payload.emoji) in self.poll_reactions[guild_id]:
                    # Appends the member to the list
                    self.poll_members[guild_id].append(member)
                    await self.fetch_poll_count(guild_id)

    # Remove the member from the list when someone removes their reaction of the message, with conditions
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild_id = payload.guild_id
        # Checks threre is a poll message or not, if yes, proceed
        if self.poll_message[guild_id] is not None:
            # Checks the payload message is equals to the poll message or not, if yes, proceed
            if payload.message_id == self.poll_message[guild_id].id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                # Checks the member is a bot or not
                if member.bot:
                    return
                elif str(payload.emoji) in self.poll_reactions[guild_id]:
                    # Remove the member from the list
                    self.poll_members[guild_id].remove(member)
                    await self.fetch_poll_count(guild_id)

    # Creates a poll
    @poll.command(name='create', description='Creates a poll')
    async def poll_create(self, interaction: Interaction, mode: Option(str, choices=poll_mode, description="Poll mode", required=True), title: str, question: str, options: str):
        guild_id = interaction.guild.id
        while True:
            if self.poll_message[guild_id] is not None:
                await self.poll_reset_confirm_msg(interaction, message="You have already created a poll before in this guild! Are you sure you want to reset it before creating a new one?")
                if self.reset_confirm_option[guild_id] == "no_button02":
                    break
                elif self.reset_confirm_option[guild_id] == "yes_button01":
                    self.reset_confirm_option[guild_id] = None
            else:
                if not mode in poll_mode or (mode != poll_mode[0] and options is None):
                    return await interaction.response.send_message("Looks like the mode u entered is not a valid mode...")
                elif mode == poll_mode[0] and options is None:
                    return await interaction.response.send_message("Please enter something in the options.")
                await interaction.response.defer()
                self.poll_members[guild_id] = []
                poll_embed = discord.Embed(title=title, description=question, color=interaction.author.colour)
                if mode == poll_mode[0]:
                    options_list = options.split(", ")
                    self.poll_options[guild_id] = options_list
                    poll_embed.add_field(name="Choose an option:", value="", inline=False)
                    for i in range(len(self.poll_options[guild_id])):
                        poll_embed.add_field(name=f'{poll_emojis[i]}：{self.poll_options[guild_id][i]}', value='\u200b', inline=False)
                else:
                    self.poll_options[guild_id] = poll_emojis[-2:]
                self.poll_message[guild_id] = await interaction.followup.send(embed=poll_embed)
                await interaction.followup.send("Poll created.", ephemeral=True, delete_after=0)
                if mode == poll_mode[0]:
                    for i in range(len(self.poll_options[guild_id])):
                        await self.poll_message[guild_id].add_reaction(poll_emojis[i])
                        self.poll_reactions[guild_id].append(poll_emojis[i])
                else:
                    for i in range(2):
                        await self.poll_message[guild_id].add_reaction(poll_emojis[i + 10])
                        self.poll_reactions[guild_id].append(poll_emojis[i + 10])
                self.poll_type[guild_id] = mode
                await self.fetch_poll_count(guild_id)
                break
                
    # Adds an option to an exsisting poll
    @poll.command(name='add', description='Adds an option to the poll')
    async def poll_add(self, interaction: Interaction, option: str):
        guild_id = interaction.guild.id
        await interaction.response.send_message("Appending option...", ephemeral=True, delete_after=0)
        self.poll_options[guild_id].append(option)
        emoji_index = len(self.poll_reactions[guild_id]) + 1
        self.poll_reactions[guild_id].append(poll_emojis[emoji_index])
        poll_add_embed = discord.Embed(title=self.poll_message[guild_id].embeds[0].title, description=self.poll_message[guild_id].embeds[0].description, color=interaction.author.colour)
        poll_add_embed.add_field(name="Choose an option:", value="", inline=False)
        for i in range(len(self.poll_options[guild_id])):
            poll_add_embed.add_field(name=f'{poll_emojis[i]}：{self.poll_options[guild_id][i]}', value='\u200b', inline=False)
        poll_add_embed.set_footer(text=f'Poll edited by {interaction.author.display_name}', icon_url=interaction.author.avatar.url)
        await self.poll_message[guild_id].edit(embed=poll_add_embed)
        for i in range(len(self.poll_options[guild_id])):
            await self.poll_message[guild_id].add_reaction(poll_emojis[i])
        
    # Removes an option from an exsisting poll
    @poll.command(name='remove', description='Removes an option from the poll')
    async def poll_remove(self, interaction: Interaction, poll_option_number: str):
        guild_id = interaction.guild.id
        await interaction.response.send_message("Removing option...", ephemeral=True, delete_after=0)
        self.poll_options[guild_id].pop(int(poll_option_number) - 1)
        cache_message = get(self.bot.cached_messages, id=self.poll_message[guild_id].id)
        reaction = get(cache_message.reactions, emoji=self.poll_reactions[guild_id][int(poll_option_number) - 1])
        self.poll_reactions[guild_id].pop(int(poll_option_number) - 1)
        remove_embed = discord.Embed(title=self.poll_message[guild_id].embeds[0].title, description=self.poll_message[guild_id].embeds[0].description, color=interaction.author.colour)
        remove_embed.add_field(name="Choose an option:", value="", inline=False)
        for i in range(len(self.poll_options[guild_id])):
            remove_embed.add_field(name=f'{self.poll_reactions[guild_id][i]}：{self.poll_options[guild_id][i]}', value='\u200b', inline=False)
        remove_embed.set_footer(text=f'Poll edited by {interaction.author.display_name}', icon_url=interaction.author.avatar.url)
        await self.poll_message[guild_id].edit(embed=remove_embed)
        # Gets the cached message and removes the reaction from it
        async for user in reaction.users():
            await reaction.remove(user)

    # End and shows the result of the poll
    @poll.command(name='results', description='Shows the results of the poll')
    async def poll_results(self, interaction: Interaction):
        guild_id = interaction.guild.id
        await interaction.response.send_message("Ended the poll.", ephemeral=True, delete_after=0)
        result_embed = discord.Embed(title=self.poll_message[guild_id].embeds[0].title, description=self.poll_message[guild_id].embeds[0].description, color=interaction.author.colour)
        result_embed.timestamp = datetime.now()
        result_embed.set_footer(text=f'Poll ended by {interaction.author.display_name}', icon_url=interaction.author.avatar.url)
        result_embed.add_field(name='Results', value='\u200b', inline=False)
        if self.poll_type[guild_id] == "Options":
            try:
                for emojis in self.poll_reactions[guild_id]:
                    self.total_votes[guild_id] += self.poll_count[guild_id][emojis]
            except KeyError:
                pass
            for i in range(len(self.poll_options[guild_id])):
                try:
                    percentage = f"{round(((self.poll_count[guild_id][self.poll_reactions[guild_id][i]] / self.total_votes[guild_id]) * 100), 2)}%"
                except ZeroDivisionError:
                    percentage = f"{round(0, 2)}%"
                if self.poll_count[guild_id][self.poll_reactions[guild_id][i]] == 0 or self.poll_count[guild_id][self.poll_reactions[guild_id][i]] > 1:
                    result_embed.add_field(name=f'{self.poll_reactions[guild_id][i]}：{self.poll_options[guild_id][i]}', value=f'{self.poll_count[guild_id][self.poll_reactions[guild_id][i]]} votes ({percentage})', inline=False)
                else:
                    result_embed.add_field(name=f'{self.poll_reactions[guild_id][i]}：{self.poll_options[guild_id][i]}', value=f'{self.poll_count[guild_id][self.poll_reactions[guild_id][i]]} vote ({percentage})', inline=False)
        elif self.poll_type[guild_id] == "Like/Dislike":
            try:
                for emojis in poll_emojis[-2:]:
                    self.total_votes[guild_id] += self.poll_count[guild_id][emojis]
            except KeyError:
                pass
            for i in range(len(self.poll_options[guild_id])):
                try:
                    percentage = f"{round(((self.poll_count[guild_id][self.poll_reactions[guild_id][i]] / self.total_votes[guild_id]) * 100), 2)}%"
                except ZeroDivisionError:
                    percentage = f"{round(0, 2)}%"
                if self.poll_count[guild_id][self.poll_options[guild_id][i]] == 0 or self.poll_count[guild_id][self.poll_options[guild_id][i]] > 1:
                    result_embed.add_field(name=f'{self.poll_options[guild_id][i]}：', value=f'{self.poll_count[guild_id][self.poll_options[guild_id][i]]} votes ({percentage})', inline=False)
                else:
                    result_embed.add_field(name=f'{self.poll_options[guild_id][i]}：', value=f'{self.poll_count[guild_id][self.poll_options[guild_id][i]]} vote ({percentage})', inline=False)
        for members in interaction.guild.members:
            if members.bot is not True:
                self.total_members[guild_id].append(members)
        try:
            self.reaction_rate[guild_id] = f"{round((len(self.poll_members[guild_id]) / len(self.total_members[guild_id])) * 100, 2)}%"
        except ZeroDivisionError:
            self.reaction_rate[guild_id] = f"{round(0, 2)}%"
        result_embed.add_field(name='', value='\u200b', inline=False)
        result_embed.add_field(name=f'Number of total votes: {self.total_votes[guild_id]}', value='', inline=False)
        result_embed.add_field(name=f'Reaction rate: {self.reaction_rate[guild_id]}', value='\u200b', inline=False)
        await self.poll_message[guild_id].edit(embed=result_embed)
        await self.reset(interaction)
      
# ----------</Poll>----------


def setup(bot):
    bot.add_cog(Poll(bot))
