import discord
from discord import SlashCommandGroup, Interaction, Option
from discord.ext import commands
from discord.ext.commands import MissingPermissions


class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    unmute = SlashCommandGroup("unmute", "Unmute people")

    # ----------<Unmutes a member from text or voice channel>----------

    # Unmutes a member from text
    @unmute.command(name="text", description="Unmutes a member from text channels")
    @commands.has_guild_permissions(moderate_members=True)
    async def unmute_text(self, interaction: Interaction, member: Option(discord.Member, required=True), reason: Option(str, required=False)):
        muted = discord.utils.get(interaction.guild.roles, name="Muted")
        if muted not in member.roles:
            await interaction.response.send_message(f"<@{member.id}> is not muted!", ephemeral=True)
            return
        else:
            if reason is None:
                await member.remove_roles(muted)
                await interaction.response.send_message(f"<@{member.id}> has been unmuted from text by <@{interaction.author.id}>.")
            else:
                await member.remove_roles(muted, reason=reason)
                await interaction.response.send_message(f"<@{member.id}> has been unmuted from text by <@{interaction.author.id}>. Reason: {reason}.")

    @unmute_text.error
    async def unmute_text_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # Unmutes a member from voice
    @unmute.command(name="voice", description="Unmutes a member from voice channels")
    @commands.has_guild_permissions(moderate_members=True)
    async def unmute_voice(self, interaction: Interaction, member: Option(discord.Member, required=True), reason: Option(str, required=False)):
        if reason is None:
            await member.edit(mute=False)
            await interaction.response.send_message(f"<@{member.id}> has been unmuted from voice by <@{interaction.author.id}>.")
        else:
            await member.edit(mute=False, reason=reason)
            await interaction.response.send_message(f"<@{member.id}> has been unmuted from voice by <@{interaction.author.id}>. Reason: {reason}.")

    @unmute_voice.error
    async def unmute_voice_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("You cannot do this without moderate members permissions!")
        else:
            raise error

    # ----------</Unmutes a member from text or voice channel>----------


def setup(bot):
    bot.add_cog(Unmute(bot))
