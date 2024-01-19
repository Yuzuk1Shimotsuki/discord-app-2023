import discord
from discord import Interaction, Option
from discord.ext import commands


class DisplayUserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Display avatar or user info>----------

    # Displaing an avatar of a user to everyone
    @commands.slash_command(description="Displays your avatar or someone else's avatar to everyone.")
    async def avatar(self, interaction: Interaction, user: Option(discord.User, name="user", description="The user to get avatar for", required=False)):
        user = user or interaction.author
        # Using property avatar will cause an error if the user have not set a custom avatar
        userAvatar = user.display_avatar.url
        embedAvatar = discord.Embed(title="Avatar Link", url=userAvatar)
        embedAvatar.set_image(url=userAvatar)
        embedAvatar.set_author(name=user.display_name, icon_url=userAvatar)
        embedAvatar.set_footer(text=f"Requested by {interaction.author.display_name}", icon_url=interaction.author.display_avatar.url)
        await interaction.response.send_message(embed=embedAvatar)

    # Displaing the info of you or a specfied user to everyone
    @commands.slash_command(
        description="Displays information about yourself or another user, such as ID and joined date.")
    async def user(self, interaction: Interaction, user: Option(discord.User, name="user", description="The user to get info about", required=False)):
        user = user or interaction.author
        embedinfo = discord.Embed()
        embedinfo.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embedinfo.set_thumbnail(url=user.avatar.url)
        embedinfo.add_field(name="Name:", value=user.name)
        embedinfo.add_field(name="Joined Discord on:",
                            value=f"**{discord.utils.format_dt(user.created_at, style='R')}**")
        embedinfo.add_field(name="Joined Server on:",
                            value=f"**{discord.utils.format_dt(user.joined_at, style='R')}**")
        embedinfo.set_footer(text=f"Requested by {interaction.author.display_name}", icon_url=interaction.author.display_avatar.url)
        await interaction.response.send_message(embed=embedinfo)

    # ----------</Display avatar or user info>----------


def setup(bot):
    bot.add_cog(DisplayUserInfo(bot))
