import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.utils import get
from datetime import datetime
from typing import Optional

vote_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "👍", "👎"]


class ResetConfirm(discord.ui.View):
    # "Yes" button
    @discord.ui.button(label="Yes", row=0, custom_id="yes_button01", style=discord.ButtonStyle.danger)
    async def first_button_callback(self, button, interaction):
        await interaction.response.edit_message(content="The vote has been reset.", view=None)

    # "No" button
    @discord.ui.button(label="No", row=0, custom_id="no_button02", style=discord.ButtonStyle.secondary)
    async def second_button_callback(self, button, interaction):
        await interaction.response.edit_message(content="The reset was aborted.", view=None)


class Vote(commands.Cog):
    def __init__(self, bot):
        global vote_emojis
        self.bot = bot
        self.vote_message = {}
        self.vote_options = {}
        self.vote_reactions = {}
        self.vote_count = {}
        self.vote_type = {}
        self.total_members = {}
        self.voted_members = {}
        self.total_votes = {}
        self.reaction_rate = {}
        self.reset_confirm_message = {}
        self.reset_confirm_option = {}


    vote = app_commands.Group(name="vote", description="Poll commands")

    # ----------<Poll>----------

    # Startup
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            guild_id = int(guild.id)
            self.vote_message[guild_id] = None
            self.vote_options[guild_id] = None
            self.vote_reactions[guild_id] = []
            self.vote_count[guild_id] = {}
            self.vote_type[guild_id] = None
            self.total_members[guild_id] = []
            self.voted_members[guild_id] = []
            self.total_votes[guild_id] = 0
            self.reaction_rate[guild_id] = 0
            self.reset_confirm_message[guild_id] = None
            self.reset_confirm_option[guild_id] = None

    # Function of resetting a vote
    async def reset(self, interaction: Interaction):
        guild_id = interaction.guild.id
        self.vote_message[guild_id] = None
        self.vote_options[guild_id] = None
        self.vote_reactions[guild_id] = []
        self.vote_count[guild_id] = {}
        self.vote_type[guild_id] = None
        self.total_members[guild_id] = []
        self.voted_members[guild_id] = []
        self.total_votes[guild_id] = 0
        self.reaction_rate[guild_id] = 0
        self.reset_confirm_message[guild_id] = None
        self.reset_confirm_option[guild_id] = None

    # Confirming reset
    async def vote_reset_confirm_msg(self, interaction: Interaction, message: str):
        guild_id = interaction.guild.id
        if message is None:
            message = "Are you sure you want to reset the vote?"
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

    # Reset the vote
    @vote.command(name="reset", description="Reset the vote")
    async def vote_reset(self, interaction: Interaction):
        if self.vote_message is not None:
            await self.vote_reset_confirm_msg(interaction, None)
        else:
            await interaction.response.send_message("There is currently no voting needs to reset.", ephemeral=True)

    # Fetching the amount 
    async def fetch_voted_count(self, guild_id):
        for emojis in vote_emojis:
            cache_message = get(self.bot.cached_messages, id=self.vote_message[guild_id].id)
            reaction = get(cache_message.reactions, emoji=emojis)
            try:
                self.vote_count[guild_id][f"{emojis}"] = reaction.count - 1
            except AttributeError:
                pass

    # Appends a member to the list when someone reacts the message, with conditions
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = payload.guild_id
        # Checks threre is a vote message or not, if yes, proceed
        if self.vote_message[guild_id] is not None:
            # Checks the payload message is equals to the vote message or not, if yes, proceed
            if payload.message_id == self.vote_message[guild_id].id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                # Checks the member is a bot or not
                if member.bot:
                    return
                if member in self.voted_members[guild_id]:
                    # This member is already in the list
                    # Remove the lastest reaction done by the member
                    self.voted_members[guild_id].append(member)
                    await self.vote_message[guild_id].remove_reaction(payload.emoji, member)
                elif str(payload.emoji) in self.vote_reactions[guild_id]:
                    # Appends the member to the list
                    self.voted_members[guild_id].append(member)
                    await self.fetch_voted_count(guild_id)

    # Remove the member from the list when someone removes their reaction of the message, with conditions
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild_id = payload.guild_id
        # Checks threre is a vote message or not, if yes, proceed
        if self.vote_message[guild_id] is not None:
            # Checks the payload message is equals to the vote message or not, if yes, proceed
            if payload.message_id == self.vote_message[guild_id].id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                # Checks the member is a bot or not
                if member.bot:
                    return
                elif str(payload.emoji) in self.vote_reactions[guild_id]:
                    # Remove the member from the list
                    self.voted_members[guild_id].remove(member)
                    await self.fetch_voted_count(guild_id)

    # Creates a vote
    @vote.command(name='create', description='Creates a vote')
    @app_commands.describe(mode="Voting mode")
    @app_commands.describe(title="Title of the vote")
    @app_commands.describe(question="Question of the vote")
    @app_commands.describe(options="Options of the vote (Enter options by seperated with a comma e.g. option1, option2, ..., option10)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Options", value="options"),
        app_commands.Choice(name="Like/Dislike", value="ratio")
        ])
    async def vote_create(self, interaction: Interaction, mode: app_commands.Choice[str], title: str, question: Optional[str] = None, options: Optional[str] = None):
        guild_id = interaction.guild.id
        if self.vote_message[guild_id] is None:
            await interaction.response.defer()
        while True:
            if self.vote_message[guild_id] is not None:
                await self.poll_reset_confirm_msg(interaction, message="You have already created a vote before in this guild! Are you sure you want to reset it before creating a new one?")
                if self.reset_confirm_option[guild_id] == "no_button02":
                    break
                elif self.reset_confirm_option[guild_id] == "yes_button01":
                    self.reset_confirm_option[guild_id] = None
            else:
                if mode.value != "options" and options is None:
                    return await interaction.followup.send("Looks like the mode u entered is not a valid mode :thinking: ...")
                elif mode.value == "options" and options is None:
                    return await interaction.followup.send("Enter some options for me pwease :pleading_face:")
                self.voted_members[guild_id] = []
                vote_embed = discord.Embed(title=title, description=question, color=interaction.user.colour)
                if mode.value == "options":
                    options_list = options.split(", ")
                    if len(options_list) > 10:
                        return await interaction.followup.send(f"Looks like the number of options u entered exceeded the maximum limit :thinking: ... ({len(options_list)} out of 10)")
                    self.vote_options[guild_id] = options_list
                    vote_embed.add_field(name="Choose an option:", value="", inline=False)
                    for i in range(len(self.vote_options[guild_id])):
                        vote_embed.add_field(name=f'{vote_emojis[i]}：{self.vote_options[guild_id][i]}', value='\u200b', inline=False)
                else:
                    self.vote_options[guild_id] = vote_emojis[-2:]
                self.vote_message[guild_id] = await interaction.followup.send(embed=vote_embed)
                msg = await interaction.followup.send("Poll created.", ephemeral=True, silent=True)
                await msg.delete()
                if mode.value == "options":
                    for i in range(len(self.vote_options[guild_id])):
                        await self.vote_message[guild_id].add_reaction(vote_emojis[i])
                        self.vote_reactions[guild_id].append(vote_emojis[i])
                else:
                    for i in range(2):
                        await self.vote_message[guild_id].add_reaction(vote_emojis[i + 10])
                        self.vote_reactions[guild_id].append(vote_emojis[i + 10])
                self.vote_type[guild_id] = mode.value
                await self.fetch_poll_count(guild_id)
                break
                
    # Adds an option to an exsisting vote
    @vote.command(name='add', description='Adds an option to the vote')
    @app_commands.describe(option="The option you want to append")
    async def vote_add(self, interaction: Interaction, option: str):
        guild_id = interaction.guild.id
        if self.vote_message[guild_id] is not None:
            if self.vote_type[guild_id] == "options":
                await interaction.response.send_message("Appending option...", ephemeral=True, delete_after=0)
                self.vote_options[guild_id].append(option)
                emoji_index = len(self.vote_reactions[guild_id]) + 1
                self.vote_reactions[guild_id].append(vote_emojis[emoji_index])
                poll_add_embed = discord.Embed(title=self.vote_message[guild_id].embeds[0].title, description=self.vote_message[guild_id].embeds[0].description, color=interaction.user.colour)
                poll_add_embed.add_field(name="Choose an option:", value="", inline=False)
                for i in range(len(self.vote_options[guild_id])):
                    poll_add_embed.add_field(name=f'{vote_emojis[i]}：{self.vote_options[guild_id][i]}', value='\u200b', inline=False)
                poll_add_embed.set_footer(text=f'Poll edited by {interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
                await self.vote_message[guild_id].edit(embed=poll_add_embed)
                for i in range(len(self.vote_options[guild_id])):
                    await self.vote_message[guild_id].add_reaction(vote_emojis[i])
            else:
                # Unsupported type
                await interaction.response.send_message("Appending options are not supported on this type of vote.")
        else:
            # No vote was going on in this server
            await interaction.response.send_message("No vote was going on in this server.")

    # Removes an option from an exsisting vote
    @vote.command(name='remove', description='Removes an option from the vote')
    @app_commands.describe(poll_option_number="The option you want to remove (Enter option number e.g. 5)")
    @app_commands.rename(poll_option_number="number")
    async def vote_remove(self, interaction: Interaction, poll_option_number: int):
        guild_id = interaction.guild.id
        if self.vote_message[guild_id] is not None:
            if self.vote_type[guild_id] == "options":
                await interaction.response.send_message("Removing option...", ephemeral=True, delete_after=0)
                self.vote_options[guild_id].pop(poll_option_number - 1)
                cache_message = get(self.bot.cached_messages, id=self.vote_message[guild_id].id)
                reaction = get(cache_message.reactions, emoji=self.vote_reactions[guild_id][poll_option_number - 1])
                self.vote_reactions[guild_id].pop(poll_option_number - 1)
                remove_embed = discord.Embed(title=self.vote_message[guild_id].embeds[0].title, description=self.vote_message[guild_id].embeds[0].description, color=interaction.user.colour)
                remove_embed.add_field(name="Choose an option:", value="", inline=False)
                for i in range(len(self.vote_options[guild_id])):
                    remove_embed.add_field(name=f'{self.vote_reactions[guild_id][i]}：{self.vote_options[guild_id][i]}', value='\u200b', inline=False)
                remove_embed.set_footer(text=f'Poll edited by {interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
                await self.vote_message[guild_id].edit(embed=remove_embed)
                # Gets the cached message and removes the reaction from it
                if reaction is not None:
                    async for user in reaction.users():
                        await reaction.remove(user)
            else:
                # Unsupported type
                await interaction.response.send_message("Removing options are not supported on this type of vote.")
        else:
            # No vote was going on in this server
            await interaction.response.send_message("No vote was going on in this server.")
        
    # End and shows the result of the vote
    @vote.command(name='results', description='Shows the results of the vote')
    async def vote_results(self, interaction: Interaction):
        guild_id = interaction.guild.id
        if self.vote_message[guild_id] is not None:
            await interaction.response.send_message("Ended the vote.", ephemeral=True, delete_after=0)
            result_embed = discord.Embed(title=self.vote_message[guild_id].embeds[0].title, description=self.vote_message[guild_id].embeds[0].description, color=interaction.user.colour)
            result_embed.timestamp = datetime.now()
            result_embed.set_footer(text=f'Poll ended by {interaction.user.display_name}', icon_url=interaction.user.display_avatar.url)
            result_embed.add_field(name='Results', value='\u200b', inline=False)
            if self.vote_type[guild_id] == "options":
                try:
                    for emojis in self.vote_reactions[guild_id]:
                        self.total_votes[guild_id] += self.vote_count[guild_id][emojis]
                except KeyError:
                    pass
                for i in range(len(self.vote_options[guild_id])):
                    try:
                        percentage = f"{round(((self.vote_count[guild_id][self.vote_reactions[guild_id][i]] / self.total_votes[guild_id]) * 100), 2)}%"
                    except ZeroDivisionError:
                        percentage = f"{round(0, 2)}%"
                    if self.vote_count[guild_id][self.vote_reactions[guild_id][i]] == 0 or self.vote_count[guild_id][self.vote_reactions[guild_id][i]] > 1:
                        result_embed.add_field(name=f'{self.vote_reactions[guild_id][i]}：{self.vote_options[guild_id][i]}', value=f'{self.vote_count[guild_id][self.vote_reactions[guild_id][i]]} votes ({percentage})', inline=False)
                    else:
                        result_embed.add_field(name=f'{self.vote_reactions[guild_id][i]}：{self.vote_options[guild_id][i]}', value=f'{self.vote_count[guild_id][self.vote_reactions[guild_id][i]]} vote ({percentage})', inline=False)
            elif self.vote_type[guild_id] == "ratio":
                try:
                    for emojis in vote_emojis[-2:]:
                        self.total_votes[guild_id] += self.vote_count[guild_id][emojis]
                except KeyError:
                    pass
                for i in range(len(self.vote_options[guild_id])):
                    try:
                        percentage = f"{round(((self.vote_count[guild_id][self.vote_reactions[guild_id][i]] / self.total_votes[guild_id]) * 100), 2)}%"
                    except ZeroDivisionError:
                        percentage = f"{round(0, 2)}%"
                    if self.vote_count[guild_id][self.vote_options[guild_id][i]] == 0 or self.vote_count[guild_id][self.vote_options[guild_id][i]] > 1:
                        result_embed.add_field(name=f'{self.vote_options[guild_id][i]}：', value=f'{self.vote_count[guild_id][self.vote_options[guild_id][i]]} votes ({percentage})', inline=False)
                    else:
                        result_embed.add_field(name=f'{self.vote_options[guild_id][i]}：', value=f'{self.vote_count[guild_id][self.vote_options[guild_id][i]]} vote ({percentage})', inline=False)
            for members in interaction.guild.members:
                if members.bot is not True:
                    self.total_members[guild_id].append(members)
            try:
                self.reaction_rate[guild_id] = f"{round((len(self.voted_members[guild_id]) / len(self.total_members[guild_id])) * 100, 2)}%"
            except ZeroDivisionError:
                self.reaction_rate[guild_id] = f"{round(0, 2)}%"
            result_embed.add_field(name='', value='\u200b', inline=False)
            result_embed.add_field(name=f'Number of total votes: {self.total_votes[guild_id]}', value='', inline=False)
            result_embed.add_field(name=f'Reaction rate: {self.reaction_rate[guild_id]}', value='\u200b', inline=False)
            await self.vote_message[guild_id].edit(embed=result_embed)
            await self.reset(interaction)
        else:
            # No vote was going on in this server
            await interaction.response.send_message("No vote was going on in this server.")
      
# ----------</Poll>----------


async def setup(bot):
    await bot.add_cog(Vote(bot))
