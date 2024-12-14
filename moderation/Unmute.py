import discord
from discord import app_commands, Embed, Interaction
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.ext.commands import MissingPermissions
from typing import Optional


class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cluster()

    # ----------<Unmutes a member from text channel>----------

    @app_commands.command(description="Unmutes a member from text channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @app_commands.describe(member="Member to unmute (e.g., mention or ID)")
    @app_commands.describe(reason="Reason for unmute")
    async def unmute(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        database = self.db.moderation_mute
        mute_text_collection = database["mute_text"]
        unmute_embed = Embed(title="", color=interaction.user.color)
        unmute_error_embed = Embed(title="", color=discord.Colour.red())

        # Fetch mute record from the database
        mute_record = await mute_text_collection.find_one({"guild_id": interaction.guild.id, "user_id": member.id})

        if not mute_record:
            # If no mute record is found in the database, the user is not muted
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not currently muted** in the database.", inline=False)
            return await interaction.response.send_message(embed=unmute_error_embed, ephemeral=True)

        # Retrieve the Muted role from the database record
        muted_role = interaction.guild.get_role(mute_record["role_id"])
        if not muted_role:
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> The **Muted** role no longer exists in this server. Please recreate it.", inline=False)
            return await interaction.response.send_message(embed=unmute_error_embed, ephemeral=True)

        # Check if the user actually has the Muted role
        if muted_role not in member.roles:
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} does not have the `Muted` role, but they are recorded as muted in the database.", inline=False)
            return await interaction.response.send_message(embed=unmute_error_embed, ephemeral=True)

        # Remove the Muted role
        try:
            if reason is None:
                await member.remove_roles(muted_role)
                unmute_embed.add_field(name="", value=f"{member.mention} has been **unmuted**.")
                
            else:
                await member.remove_roles(muted_role, reason=reason)
                unmute_embed.add_field(name="", value=f"{member.mention} has been **unmuted**.\nReason: **{reason}**.")

        except discord.Forbidden:
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **unmute** {member.mention}. Please check my **permissions** and **role position**.", inline=False)
            return await interaction.response.send_message(embed=unmute_error_embed, ephemeral=True)

        # Remove the mute record from the database
        await mute_text_collection.delete_one({"_id": mute_record["_id"]})

        # Send confirmation message
        await interaction.response.send_message(embed=unmute_embed)

    @unmute.error
    async def unmute_error(self, interaction: Interaction, error):
        unmute_error_embed = Embed(title="", color=discord.Colour.red())
        
        if isinstance(error, MissingPermissions):
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.", inline=False)
            await interaction.response.send_message(embed=unmute_error_embed, ephemeral=True)
        
        elif isinstance(error, BotMissingPermissions):
            unmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **unmute** that user. Please **double-check** my **permissions** and **role position**.", inline=False)
            await interaction.response.send_message(embed=unmute_error_embed, ephemeral=True)
        
        else:
            raise error

    # ----------</Unmutes a member from text channel>----------

async def setup(bot):
    await bot.add_cog(Unmute(bot))
    