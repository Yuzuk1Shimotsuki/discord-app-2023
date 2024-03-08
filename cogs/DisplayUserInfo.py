import discord
from discord import app_commands, Interaction
from discord.ext import commands
from typing import Optional


class DisplayUserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------<Display avatar or user info>----------

    # Displaing an avatar of a user to everyone
    @app_commands.command(description="Displays your avatar or someone else's avatar to everyone.")
    @app_commands.describe(user="The user to get avatar for")
    async def avatar(self, interaction: Interaction, user: Optional[discord.User] = None):
        user = user or interaction.user
        userAvatar = user.display_avatar.url
        embed = discord.Embed(title="Avatar Link", url=userAvatar)
        embed.set_image(url=f"{userAvatar}")
        embed.set_author(name=f"{user.display_name}", icon_url=f"{userAvatar}")
        embed.set_footer(text=f'Requested by {interaction.user.display_name}', icon_url=f"{interaction.user.display_avatar.url}")
        await interaction.response.send_message(embed=embed)

    # Displaing the info of you or a specfied user to everyone
    @app_commands.command(description="Displays information about yourself or another member in the server, such as ID and joined date.")
    @app_commands.describe(member="The user to get info about")
    async def user(self, interaction: Interaction, member: Optional[discord.Member] = None):
            member = member or interaction.user
            embedinfo = discord.Embed()
            embedinfo.set_author(name=f"{member.name}", icon_url=f"{member.display_avatar.url}")
            embedinfo.set_thumbnail(url=member.display_avatar.url)
            embedinfo.add_field(name="Guild Name:", value=member.display_name)
            embedinfo.add_field(name="Joined Discord on:",
                                value=f"**{discord.utils.format_dt(member.created_at, style='R')}**")
            embedinfo.add_field(name="Joined Server on:",
                                value=f"**{discord.utils.format_dt(member.joined_at, style='R')}**")
            embedinfo.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embedinfo)

    @user.error
    async def user_error(self, interaction: Interaction, error):
        if isinstance(error, discord.app_commands.errors.TransformerError):
            if str(error).startswith("Failed to convert") and str(error).endswith("to Member"):
                # The required user is not in the server
                return await interaction.response.send_message(f'Looks like <@{interaction.namespace.member.id}> is not in the server :thinking:...')
            else:
                raise error
        else:
            raise error

    # ----------</Display avatar or user info>----------


async def setup(bot):
    await bot.add_cog(DisplayUserInfo(bot))
