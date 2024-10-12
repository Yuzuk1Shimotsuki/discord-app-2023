import discord
from discord import app_commands, Interaction
from discord.ext import commands
from discord.ui import Modal, TextInput
from typing import Optional

def image_url_check(url):
    supported_format = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"]
    if supported_format in url:
        return True
    return False

class CustomEmbedModal(Modal, title = "Customize your embed"):
    # TextInput Item
    title = TextInput(label = "Title", required=True)
    url = TextInput(label = "URL for the embed")
    description = TextInput(label = "Description")
    name = TextInput(label = "Name (separate with \n for a new field)", required=True)
    text_value = TextInput(label = "Text value (separate with \f for a new field)", required=True)
    image_url = TextInput(label = "Image URL (optional)")
    thumbnail_url = TextInput(label = "Thumbnail URL (optional)")
    author_name = TextInput(label = "Author Name (optional)")
    author_url = TextInput(label = "Author URL (optional)")
    author_image_url = TextInput(label = "Author Image URL (optional)")
    footer = TextInput(label = "Footer (optional)")
    footer_image_url = TextInput(label = "Footer Image URL (optional)")

    # Callback Modal
    async def on_submit(self, interaction: discord.Interaction):
        custom_embed = discord.Embed(title=self.title, description=self.description, color=interaction.namespace.color, url=self.url)
        image_checklist = ["image_url", "thumbnail_url", "author_image_url", "footer_image_url"]
        # Check the image is valid or not
        for image in image_checklist:
            if self.__getattribute__(image) is not None and not image_url_check(self.__getattribute__(image)): 
                return await interaction.response.send_message("Invalid image URL. Must be an image URL that starts with http or https and ends in: jpg, jpeg, png, gif, webp")
        namelist = str(self.name).split("\n")
        textlist = str(self.text_value).split("\f")
        if len(namelist) != len(textlist):
            return await interaction.response.send_message("Invalid format. Number of lines of name should be equal to number of line of text.")
        for i in range(len(namelist)):
            custom_embed.add_field(name=namelist[i], value=textlist[i], inline=True)
        if self.image_url is not None:
            custom_embed.set_image(url=self.image_url)
        if self.thumbnail_url is not None:
            custom_embed.set_thumbnail(url=self.thumbnail_url)
        if self.author_name is not None and self.author_url is not None and self.author_image_url is not None:
            custom_embed.set_author(name=self.author_name, url=self.author_url, icon_url=self.author_image_url)
        if self.author_name is not None and self.author_url is not None:
            custom_embed.set_author(name=self.author_name, url=self.author_url)
        if self.author_name is not None:
            custom_embed.set_author(name=self.author_name)
        if self.footer is not None and self.footer_image_url is not None:
            custom_embed.set_footer(text=self.footer, icon_url=self.footer_image_url)
        if self.footer is not None:
            custom_embed.set_footer(text=self.footer)
        await interaction.response.send_message(embed=custom_embed)


class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Displaing an avatar of a user to everyone
    @app_commands.command(description="Creates a custom embed")
    @app_commands.describe(user="Color of the embed. Defaults to user's role color if empty.")
    async def embed(self, interaction: Interaction, color: Optional[discord.Color] = None):
        if color is None and interaction.namespace.color is None:
            interaction.namespace.color = interaction.user.color
        await interaction.response.send_modal(CustomEmbedModal())

async def setup(bot):
    await bot.add_cog(Embed(bot))
