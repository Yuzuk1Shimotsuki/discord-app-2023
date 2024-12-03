import discord
import re
from discord import app_commands, Interaction, Embed, TextStyle
from discord.ext import commands
from discord.ui import Modal, TextInput
from datetime import datetime
from typing import Optional


def image_url_check(url_list):
    supported_formats = r'\b\w+\.(png|jpg|jpeg|gif|webp|bmp|tiff)\b'
    count = 0
    
    for url in url_list:
        if re.findall(supported_formats, url) != []:
            count += 1
    
    if count == len(url_list):
        return True
    
    return False

custom_embed = None
user_metion_pattern = r'<@(\d+)>'


# ----------<Custom Embed>----------


class CustomEmbedModal(Modal, title = "Customize your embed"):
    global custom_embed
    # TextInput Item
    name = TextInput(label = "Name (Use <i> for inline, <br> for new field)", style=TextStyle.short, required=True)
    text = TextInput(label = "Text (Separate with '<br>' for a new field)", style=TextStyle.paragraph, required=True)
    image_url = TextInput(label = "Image URL (optional)", required=False)
    thumbnail_url = TextInput(label = "Thumbnail URL (optional)", required=False)


    # Callback Modal
    async def on_submit(self, interaction: discord.Interaction):
        global custom_embed
        namelist = self.name.value.split("<br>".lower())
        textlist = self.text.value.split("<br>".lower())
        
        # Check the image is valid or not
        if self.image_url.value != "" and self.thumbnail_url.value != "" and not image_url_check([self.image_url.value, self.thumbnail_url.value]):
            return await interaction.response.send_message("Invalid image URL. Must be an image URL that starts with http or https and ends in: jpg, jpeg, png, gif, webp")
        
        if self.image_url.value != "":
            custom_embed.set_image(url=self.image_url.value)
        
        if self.thumbnail_url.value != "":
            custom_embed.set_thumbnail(url=self.thumbnail_url.value)
        
        if len(namelist) != len(textlist):
            return await interaction.response.send_message("Invalid format. Number of lines of name should be equal to number of lines of text.")
        
        for i in range(len(namelist)):
            if "<i>".lower() in namelist[i]:
                custom_embed.add_field(name=namelist[i].replace("<i>", ""), value=textlist[i], inline=True)
            
            else:
                custom_embed.add_field(name=namelist[i], value=textlist[i], inline=False)
        
        await interaction.response.send_message(embed=custom_embed)


class CustomEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def retrieve_user(self, text):
        global user_metion_pattern
        # Check for user objects
        user_id = re.findall(user_metion_pattern, text)
        
        if user_id != []:
            try:
                return await self.bot.fetch_user(user_id[0])
            
            except discord.HTTPException as e:
                if e.status == 404 and e.code == 10013:
                    # User not found
                    return None


    # Creates a custom embed
    @app_commands.command(description="Creates a custom embed")
    @app_commands.describe(title="Title for this embed.")
    @app_commands.describe(description="Description for this embed.")
    @app_commands.describe(timestamp="Show timestamp for this embed?")
    @app_commands.describe(color="Color for this embed. Defaults to user's role color if empty.")
    @app_commands.describe(url="URL link for this embed. (Optional, Acecpts both Discord user's object and string)")
    @app_commands.describe(author_name="Author name for this embed. (Optional, Acecpts both Discord user's object and string)")
    @app_commands.describe(author_url="Author URL link for this embed. (Optional, Acecpts both Discord user's object and string)")
    @app_commands.describe(author_image_url="Image URL link of the author for this embed. (Optional, Acecpts both Discord user's object and string)")
    @app_commands.describe(footer="Footer for this embed. (Optional, Acecpts both Discord user's object and string)")
    @app_commands.describe(author_image_url="Image URL link of the footer for this embed. (Optional, Acecpts both Discord user's object and string)")
    async def embed(self,
                    interaction: Interaction,
                    title: str,
                    description: Optional[str],
                    timestamp: bool,
                    color: Optional[str] = None,
                    url: Optional[str] = None,
                    author_name: Optional[str] = None,
                    author_url: Optional[str] = None,
                    author_image_url: Optional[str] = None,
                    footer: Optional[str] = None,
                    footer_image_url: Optional[str] = None):
        global custom_embed
        global user_metion_pattern
        
        if timestamp:
            timestamp = datetime.now()
        
        else:
            timestamp = None
        
        color = color or interaction.user.color
        
        # Check for discord.User objects
        if url is not None:
            user: discord.User = await self.retrieve_user(url)
            
            if user is not None:
                # Converts discord.User object to user's URL
                url = url.replace(f"<@{re.findall(user_metion_pattern, url)[0]}>", f"https://discordapp.com/users/{user.id}")
        
        if author_name is not None:
            user: discord.User = await self.retrieve_user(author_name)
            
            if user is not None:
                # Converts discord.User object to username
                author_name = author_name.replace(f"<@{re.findall(user_metion_pattern, author_name)[0]}>", f"{user.display_name}")
        
        if author_url is not None:
            user: discord.User = await self.retrieve_user(author_url)
            
            if user is not None:
                # Converts discord.User object to user's URL
                author_url = author_url.replace(f"<@{re.findall(user_metion_pattern, author_url)[0]}>", f"https://discordapp.com/users/{user.id}")
        
        if author_image_url is not None:
            user: discord.User = await self.retrieve_user(author_image_url)
            
            if user is not None:
                # Converts discord.User object to user's avatar URL
                author_image_url = author_image_url.replace(f"<@{re.findall(user_metion_pattern, author_image_url)[0]}>", f"{user.display_avatar.url}")
        
        if footer is not None:
            user: discord.User = await self.retrieve_user(footer)
            
            if user is not None:
                # Converts discord.User object to username
                footer = footer.replace(f"<@{re.findall(user_metion_pattern, footer)[0]}>", f"{user.display_name}")
        
        if footer_image_url is not None:
            user: discord.User = await self.retrieve_user(footer_image_url)
            
            if user is not None:
                # Converts discord.User object to user's avatar URL
                footer_image_url = footer_image_url.replace(f"<@{re.findall(user_metion_pattern, footer_image_url)[0]}>", f"{user.display_avatar.url}")
        
        # Check the image is valid or not
        if author_image_url is not None and footer_image_url is not None and not image_url_check([author_image_url, footer_image_url]): 
            return await interaction.response.send_message("Invalid image URL. Must be an image URL that starts with http or https and ends in: jpg, jpeg, png, gif, webp")
        
        custom_embed = Embed(title=title, description=description, timestamp=timestamp, color=color, url=url)
        custom_embed.set_author(name=author_name or None, url=author_url or None, icon_url=author_image_url or None)
        custom_embed.set_footer(text=footer or None, icon_url=footer_image_url or None)
        
        await interaction.response.send_modal(CustomEmbedModal())


# ----------</Custom Embed>----------


async def setup(bot):
    await bot.add_cog(CustomEmbed(bot))

