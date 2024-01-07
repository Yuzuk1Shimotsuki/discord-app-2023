import discord
from discord import Interaction
from discord.ext import commands
from discord.utils import get
from datetime import datetime


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_message = None
        self.poll_options = None
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "👍", "👎"]
        self.poll_count = {}
        self.poll_options = []
        self.poll_type = None
        self.total_members = []
        self.poll_members = []
        self.total_votes = 0
        self.reaction_rate = 0
        self.reset_confirm_message = None
        self.reset_confirm_option = None

    poll = discord.SlashCommandGroup("poll", "Poll commands")

    # ----------<Poll>----------

    # Function of resetting a poll
    async def reset(self):
        self.poll_message = None
        self.poll_options = None
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "👍", "👎"]
        self.poll_count = {}
        self.poll_options = []
        self.poll_type = None
        self.total_members = []
        self.poll_members = []
        self.total_votes = 0
        self.reaction_rate = 0
        self.reset_confirm_message = None
        self.reset_confirm_option = None

    # Confirming reset
    async def poll_reset_confirm_msg(self, interaction: Interaction, message: str):
        if message is None:
            message = "Are you sure you want to reset the poll?"
        await interaction.response.defer()

        # Class for confirm buttons
        class ResetConfirm(discord.ui.View):
            def __init__(self):
                super().__init__()

            # Reset the poll when a confirm was done by user
            async def reset(self):
                self.poll_message = None
                self.poll_options = None
                self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "👍", "👎"]
                self.poll_count = {}
                self.poll_options = []
                self.poll_type = None
                self.total_members = []
                self.poll_members = []
                self.total_votes = 0
                self.reaction_rate = 0
                self.reset_confirm_message = None
                self.reset_confirm_option = None

            # "Yes" button
            @discord.ui.button(label="Yes", row=0, custom_id="yes_button01", style=discord.ButtonStyle.danger)
            async def first_button_callback(self, button, interaction):
                await self.reset()
                await interaction.response.edit_message(content="The poll has been reset.", view=None)

            # "No" button
            @discord.ui.button(label="No", row=0, custom_id="no_button02", style=discord.ButtonStyle.secondary)
            async def second_button_callback(self, button, interaction):
                await interaction.response.edit_message(content="The reset was aborted.", view=None)

        # Displaying confirm buttons from event reset()
        view = ResetConfirm()
        self.reset_confirm_message = await interaction.followup.send(message, view=view)
        res = await self.bot.wait_for('interaction', check=lambda interaction: interaction.data[
                                                                                   "component_type"] == 2 and "custom_id" in interaction.data.keys())
        # Loop through the children of the view and get the button with corresponding custom_id
        for item in view.children:
            if item.custom_id == res.data["custom_id"]:
                button = item
        # Executing the button
        if button.custom_id == "no_button02":
            channel = self.bot.get_channel(self.reset_confirm_message.channel.id)
            msg_to_delete = await channel.fetch_message(self.reset_confirm_message.id)
            await msg_to_delete.delete()
        self.reset_confirm_option = button.custom_id

    # Reset the poll
    @poll.command(name="reset", description="Reset the poll")
    async def poll_reset(self, interaction: Interaction):
        if self.poll_message is not None:
            await self.poll_reset_confirm_msg(interaction, None)
        else:
            await interaction.response.send_message("There is currently no poll needs to reset.", ephemeral=True)

    # Fetching the amount 
    async def fetch_poll_count(self):
        for emojis in self.poll_emojis:
            cache_message = get(self.bot.cached_messages, id=self.poll_message.id)
            reaction = get(cache_message.reactions, emoji=emojis)
            try:
                self.poll_count[f"{emojis}"] = reaction.count - 1
            except AttributeError:
                pass

    # Appends a member to the list when someone reacts the message, with conditions
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Checks threre is a poll message or not, if yes, proceed
        if self.poll_message is not None:
            # Checks the payload message is equals to the poll message or not, if yes, proceed
            if payload.message_id == self.poll_message.id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                # Checks the member is a bot or not
                if member.bot:
                    return
                if member in self.poll_members:
                    # This member is already in the list
                    # Remove the lastest reaction done by the member
                    self.poll_members.append(member)
                    await self.poll_message.remove_reaction(payload.emoji, member)
                elif str(payload.emoji) in self.poll_emojis:
                    # Appends the member to the list
                    self.poll_members.append(member)
                    await self.fetch_poll_count()

    # Remove the member from the list when someone removes their reaction of the message, with conditions
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Checks threre is a poll message or not, if yes, proceed
        if self.poll_message is not None:
            # Checks the payload message is equals to the poll message or not, if yes, proceed
            if payload.message_id == self.poll_message.id:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                # Checks the member is a bot or not
                if member.bot:
                    return
                elif str(payload.emoji) in self.poll_emojis:
                    # Remove the member from the list
                    self.poll_members.remove(member)
                    await self.fetch_poll_count()

    # Creates a poll, with ratio
    @poll.command(name='ratio', description='Creates a poll')
    async def poll_ratio(self, interaction: Interaction, title: str, question: str):
        while True:
            if self.poll_message is not None:
                await self.poll_reset_confirm_msg(interaction, message="You have already created a poll before! Are you sure you want to reset the poll before creating a new one?")
                if self.reset_confirm_option == "no_button02":
                    break
                elif self.reset_confirm_option == "yes_button01":
                    self.reset_confirm_option = None
            else:
                await interaction.response.defer()
            self.poll_options = self.poll_emojis[-2:]
            embed = discord.Embed(title=title, description=question, color=interaction.author.colour)
            self.poll_message = await interaction.followup.send(embed=embed)
            await interaction.followup.send("Poll created.", ephemeral=True, delete_after=0)
            for i in range(2):
                await self.poll_message.add_reaction(self.poll_emojis[i + 10])
            self.poll_type = "Ratio"
            break

    # Creates a poll, with a maximum of 10 options
    @poll.command(name='options', description='Creates a poll')
    async def poll_options(self, interaction: Interaction, title: str, question: str, options: str):
        while True:
            if self.poll_message is not None:
                await self.poll_reset_confirm_msg(interaction, message="You have already created a poll before! Are you sure you want to reset the poll before creating a new one?")
                if self.reset_confirm_option == "no_button02":
                    break
                elif self.reset_confirm_option == "yes_button01":
                    self.reset_confirm_option = None
            else:
                await interaction.response.defer()
            options_list = options.split(", ")
            self.poll_members = []
            self.poll_options = options_list
            embed = discord.Embed(title=title, description=question, color=interaction.author.colour)
            embed.add_field(name="Choose an option:", value="", inline=False)
            for i in range(len(self.poll_options)):
                embed.add_field(name=f'{self.poll_emojis[i]}：{self.poll_options[i]}', value='\u200b', inline=False)
            self.poll_message = await interaction.followup.send(embed=embed)
            await interaction.followup.send("Poll created.", ephemeral=True, delete_after=0)
            for i in range(len(self.poll_options)):
                await self.poll_message.add_reaction(self.poll_emojis[i])
            self.poll_type = "Options"
            break

    # Adds an option to an exsisting poll
    @poll.command(name='add', description='Adds an option to the poll')
    async def poll_add(self, interaction: Interaction, poll_option: str):
        await interaction.response.send_message("Appending option...", ephemeral=True, delete_after=0)
        self.poll_options.append(poll_option)
        self.poll_emojis.append(str(len(self.poll_emojis) + 1))
        embed = discord.Embed(title=self.poll_message.embeds[0].title, description=self.poll_message.embeds[0].description, color=interaction.author.colour)
        embed.add_field(name="Choose an option:", value="", inline=False)
        for i in range(len(self.poll_options)):
            embed.add_field(name=f'{self.poll_emojis[i]}：{self.poll_options[i]}', value='\u200b', inline=False)
        await self.poll_message.edit(embed=embed)
        for i in range(len(self.poll_options)):
            await self.poll_message.add_reaction(num_emojis[i])
        embed.set_footer(text=f'Poll edited by {interaction.author.name}', icon_url=interaction.author.avatar.url)
        embed.add_field(name=f'{self.poll_emojis[-1]} {self.poll_options[-1]}', value='\u200b', inline=False)

    # Removes an option from an exsisting poll
    @poll.command(name='remove', description='Removes an option from the poll')
    async def poll_remove(self, interaction: Interaction, poll_option_number: str):
        await interaction.response.send_message("Removing option...", ephemeral=True, delete_after=0)
        self.poll_options.pop(int(poll_option_number) - 1)
        cache_message = get(self.bot.cached_messages, id=self.poll_message.id)
        reaction = get(cache_message.reactions, emoji=self.poll_emojis[int(poll_option_number) - 1])
        self.poll_emojis.pop(int(poll_option_number) - 1)
        embed = discord.Embed(title=self.poll_message.embeds[0].title, description=self.poll_message.embeds[0].description, color=interaction.author.colour)
        embed.add_field(name="Choose an option:", value="", inline=False)
        for i in range(len(self.poll_options)):
            embed.add_field(name=f'{self.poll_emojis[i]}：{self.poll_options[i]}', value='\u200b', inline=False)
        embed.set_footer(text=f'Poll edited by {interaction.author.name}', icon_url=interaction.author.avatar.url)
        await self.poll_message.edit(embed=embed)
        # Gets the cached message and removes the reaction from it
        async for user in reaction.users():
            await reaction.remove(user)

    # End and shows the result of the poll
    @poll.command(name='results', description='Shows the results of the poll')
    async def poll_results(self, interaction: Interaction):
        await interaction.response.send_message("Ended the poll.", ephemeral=True, delete_after=0)
        embed = discord.Embed(title=self.poll_message.embeds[0].title, description=self.poll_message.embeds[0].description, color=interaction.author.colour)
        embed.timestamp = datetime.now()
        embed.set_footer(text=f'Poll ended by {interaction.author.name}', icon_url=interaction.author.avatar.url)
        embed.add_field(name='Results', value='\u200b', inline=False)
        if self.poll_type == "Options":
            try:
                for emojis in self.poll_emojis:
                    self.total_votes += self.poll_count[f"{emojis}"]
            except KeyError:
                pass
            for i in range(len(self.poll_options)):
                percentage = f"{round(((self.poll_count[self.poll_emojis[i]] / self.total_votes) * 100), 2)}%"
                if self.poll_count[self.poll_emojis[i]] == 0 or self.poll_count[self.poll_emojis[i]] > 1:
                    embed.add_field(name=f'{self.poll_emojis[i]}：{self.poll_options[i]}', value=f'{self.poll_count[self.poll_emojis[i]]} votes ({percentage})', inline=False)
                else:
                    embed.add_field(name=f'{self.poll_emojis[i]}：{self.poll_options[i]}', value=f'{self.poll_count[self.poll_emojis[i]]} vote ({percentage})', inline=False)
        elif self.poll_type == "Ratio":
            try:
                for emojis in self.poll_emojis[-2:]:
                    self.total_votes += self.poll_count[f"{emojis}"]
            except KeyError:
                pass
            for i in range(len(self.poll_options)):
                percentage = f"{round(((self.poll_count[self.poll_emojis[i + 10]] / self.total_votes) * 100), 2)}%"
                if self.poll_count[self.poll_options[i]] == 0 or self.poll_count[self.poll_options[i]] > 1:
                    embed.add_field(name=f'{self.poll_options[i]}：', value=f'{self.poll_count[self.poll_options[i]]} votes ({percentage})', inline=False)
                else:
                    embed.add_field(name=f'{self.poll_options[i]}：', value=f'{self.poll_count[self.poll_options[i]]} vote ({percentage})', inline=False)
        for members in interaction.guild.members:
            if members.bot is not True:
                self.total_members.append(members)
        self.reaction_rate = f"{round((len(self.poll_members) / len(self.total_members)) * 100, 2)}%"
        embed.add_field(name='', value='\u200b', inline=False)
        embed.add_field(name=f'Number of total votes: {self.total_votes}', value='', inline=False)
        embed.add_field(name=f'Reaction rate: {self.reaction_rate}', value='\u200b', inline=False)
        await self.poll_message.edit(embed=embed)
        await self.reset()

# ----------</Poll>----------


def setup(bot):
    bot.add_cog(Poll(bot))
