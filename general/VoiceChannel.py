import discord
import asyncio
import re
import logging
import wavelink
from discord import app_commands, Embed, Interaction, Forbidden, Member, VoiceChannel
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from typing import cast, Optional, Union
from general.VoiceChannelFallbackConfig import *
from configs.Logging import setup_logger
from errorhandling.ErrorHandling import *

recording_vc = {}
logger = setup_logger('discord_bot', 'bot.log', logging.INFO)

# Main cog, heavily rewrited after wavelink implementation
class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        # General init
        global set_fallback_channel
        global recording_vc
        self.bot = bot

    move = app_commands.Group(name="move", description="Move User")


    # ----------<Voice Channels>-----------


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        global recording_vc
        # Ensure:
        # - this is a channel leave as opposed to anything else
        # Actions:
        # - Reset all settings if the bot leave or being kicked by someone else

        if member != self.bot.user:
            return

        if (
            after.channel is None and  # if this is None this is certainly a leave
            before.channel != after.channel  # if these match then this could be e.g. server deafen
        ):
            guild_id = before.channel.guild.id
            # Send fallback and reset all settings
            if guild_id in fallback_text_channel:
                left_vc = discord.Embed(title="", description="", color=self.bot.user.color)
                left_vc.add_field(name="", value="I left the voice channel.")
                await fallback_text_channel[guild_id].send(embed=left_vc, silent=True)
                del fallback_text_channel[guild_id]

            # Reset the music player
            reset_music_player(guild_id)
            recording_vc[guild_id] = None


    # General commands
    # Joining voice channel
    @app_commands.command(description="Invokes me to a voice channel")
    @app_commands.describe(channel="Channel to join. Leave this blank if you want the bot to join where you are.")
    async def join(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        join_embed = discord.Embed(title="", color=interaction.user.colour)
        voice_channel = channel

        if voice_channel is None and interaction.user.voice is not None:
            voice_channel = interaction.user.voice.channel

        if voice_channel is None:
            # The author is not in a voice channel, or not specified which voice channel the application should join
            return await interaction.response.send_message(embed=AuthorNotInVoiceError(interaction, interaction.user).return_embed())
        
        if not player:
            try:
                # Join voice channel
                player = await voice_channel.connect(cls=wavelink.Player)
                set_fallback_text_channel(interaction, interaction.channel)
                join_embed.add_field(name="", value=f"I've joined the voice channel {voice_channel.mention}")
                return await interaction.response.send_message(embed=join_embed)
            
            except discord.ClientException:
                # Something went wrong on discord or network side while joining voice channel
                join_embed.add_field(name="", value=f"I was unable to join {interaction.user.voice.channel}. Please try again.", inline=False)
                return await interaction.response.send_message(embed=join_embed)
            
        elif player.channel != voice_channel:
            # The bot has been connected to a voice channel but not as same as the author or required one

            if channel is not None:
                # The bot has been connected to a voice channel but not as same as the required one
                await interaction.response.send_message(embed=BotAlreadyInVoiceError(interaction, player.channel, voice_channel).notrequired())

            else:
                # The bot has been connected to a voice channel but not as same as the author one
                await interaction.response.send_message(embed=BotAlreadyInVoiceError(interaction, player.channel, voice_channel).notauthor())

        else:
            # The bot has been connected to the same channel as the author
            await interaction.response.send_message(embed=BotAlreadyInVoiceError(interaction, player.channel, voice_channel).same())


    # Leaving voice channel
    @app_commands.command(description="Leaving a voice channel")
    async def leave(self, interaction: Interaction):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        leaving_vc = discord.Embed(title="", description="", color=self.bot.user.color)
        leaving_vc_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if player is not None:
            # Disconnect the bot from voice channel if it has been connected
            await player.disconnect()
            leaving_vc.add_field(name="", value="Please wait a moment, I'm now leaving...", inline=False)
            await interaction.response.send_message(embed=leaving_vc, ephemeral=True, delete_after=0)

        else:
            leaving_vc_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I'm **not** in a voice channel :(", inline=False)
            # The bot is currently not in a voice channel
            await interaction.response.send_message(embed=leaving_vc_error_embed)


    # Moving all users or ends a voice call
    # Function to move all members (i.e. move them to any voice channel in the server, or use None to kick them away from the vc)

    # Asynchronously move a single member to the target voice channel (to avoid blocking issues)
    async def move_member(self, member: Member, target_channel: VoiceChannel | None, reason: str | None):
        try:
            if reason is not None:
                await member.move_to(target_channel, reason=reason)

            else:
                await member.move_to(target_channel)

            if target_channel is None:
                logger.info(f"Terminated {member.name} from voice")
            
            else:
                logger.info(f"Moved {member.name} to {target_channel.name}")

        except discord.Forbidden:
            logger.error(f"Permission error: Could not move {member.name}")
            raise
        
        except discord.HTTPException as e:
            logger.error(f"HTTP error while moving {member.name}: {e}")
            raise


    # Apply the above function for moving all users (to avoid blocking issues)
    async def move_all_members(self, interaction: Interaction, specified_vc: VoiceChannel | None, reason: str | None):
        # Getting all members in voice
        all_members = [member for channel in interaction.guild.voice_channels for member in channel.members]

        # Use asyncio.gather to move all members concurrently
        results = await asyncio.gather(
            *(self.move_member(member, specified_vc, reason) for member in all_members),
            return_exceptions=True
        )
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        failure_count = sum(1 for result in results if isinstance(result, Exception))
        return {"all_members_vc_count": len(all_members), "success_count": success_count, "failure_count": failure_count, "reason": reason}
    
    
    # Ending a voice call
    @app_commands.command(name="end", description="End the call for all voice channel(s)")
    @app_commands.checks.has_permissions(move_members=True)
    @app_commands.describe(reason="Reason to end the call")
    async def end(self, interaction: Interaction, reason: str):
        end_embed = discord.Embed(title="", color=interaction.user.colour)
        end_error_embed = discord.Embed(title="", color=discord.Colour.red())
        end_embed.add_field(name="", value=f"Ending the call for all voice channel(s)...", inline=False)
        await interaction.response.send_message(embed=end_embed)
        end_embed.remove_field(index=0)
        end_result = await self.move_all_members(interaction, None, reason)
        print(end_result)
        if end_result["success_count"] != end_result["all_members_vc_count"] and end_result["failure_count"] > 0:
            end_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Something went wrong while ending the call for all channel(s) :thinking:")
            return await interaction.edit_original_response(embed=end_error_embed)
        reason_message = f"\nReason: **{end_result["reason"]}" if reason is not None else ""
        end_embed.add_field(name="", value=f"Ended the call for all voice channel(s).{reason_message}", inline=False)
        await interaction.edit_original_response(embed=end_embed)


    @end.error
    async def end_error(self, interaction: Interaction, error):
        end_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            end_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `move members` permission, and you probably **don't have** it, {interaction.user.mention}.", inline=False)
            await interaction.response.send_message(embed=end_error_embed)
            
        else:
            raise error
    

    # Move all users to the voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="all", description="Moves all users to the specified voice channel")
    @app_commands.checks.has_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move them to. Leave this blank if you want to move them into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_all(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        move_all_embed = discord.Embed(title="", color=interaction.user.color)
        move_all_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if channel is None:

            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel

            else:
                # The author has not joined the voice channel yet
                move_all_error_embed.add_field(name="", value=f"Looks like you're currently not in a voice channel, but trying to move all connected members into the voice channel that you're connected :thinking: ...\nJust curious to know, where should I move them all into right now, {interaction.user.mention}?", inline=False)
                return await interaction.response.send_message(embed=move_all_error_embed)
            
        else:
            specified_vc = channel
            
        move_all_embed.add_field(name="", value=f"<a:LoadingCustom:1295993639641812992> Moving all users to {specified_vc.mention}...", inline=False)
        await interaction.response.send_message(embed=move_all_embed)
        move_all_embed.remove_field(index=0)
        move_all_result = await self.move_all_members(interaction, specified_vc, reason=reason)

        if move_all_result["failure_count"] == move_all_result["all_members_vc_count"]:
            move_all_error_embed.add_field(name="", value=f"It seems that no user were found in the voice channel, {interaction.user.mention} :thinking:...")
            return await interaction.edit_original_response(embed=move_all_error_embed)
        
        failure_message = f" with **{move_all_result["failure_count"]}** failed" if move_all_result["failure_count"] > 0 else ""
        reason_message = f"\nReason: **{reason}**." if reason is not None else ""
        move_all_embed.add_field(name="", value=f"**{move_all_result["success_count"]}** {"users" if move_all_result["success_count"] > 1 else "user"} has been moved to {specified_vc.mention}{failure_message}.{reason_message}", inline=False)
        await interaction.edit_original_response(embed=move_all_embed)


    @move_all.error
    async def move_all_error(self, interaction: Interaction, error):
        move_all_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            move_all_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `move members` permission, and you probably **don't have** it, {interaction.user.mention}.", inline=False)
            await interaction.response.send_message(embed=move_all_error_embed)

        else:
            raise error


    # Move an user to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="user", description="Moves a member to another specified voice channel")
    @app_commands.describe(member="Member to move")
    @app_commands.describe(channel="Channel to move user to. Leave this blank if you want to move the user into where you are.")
    @app_commands.describe(reason="Reason for move")
    @commands.has_guild_permissions(move_members=True)
    async def move_user(self, interaction: Interaction, member: discord.Member, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        move_user_embed = discord.Embed(title="", color=interaction.user.color)
        move_user_error_embed = discord.Embed(title="", color=discord.Colour.red())

        # Check the target user was in the vc or not
        if member.voice is None and interaction.user.id == self.bot.application_id:
            move_user_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I'm currently not in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=move_user_error_embed)
        
        elif interaction.user.voice is None:
            move_user_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> You're currently not in a voice channel!", inline=False)
            return await interaction.response.send_message(embed=move_user_error_embed)
        
        elif member.voice is None:
            move_user_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} currently not in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=move_user_error_embed)
        
        # Check the target vc
        if channel is None:

            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel

            else:
                # The author has not joined the voice channel yet
                move_user_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like you're currently not in a voice channel, but trying to move someone into the voice channel that you're connected :thinking: ...\nJust curious to know, where should I move {member.mention} into right now, {interaction.user.mention}?", inline=False)
                return await interaction.response.send_message(embed=move_user_error_embed)
            
        else:
            specified_vc = channel

        if reason is None:
            await member.move_to(specified_vc)

            if interaction.user.id == self.bot.application_id:
                move_user_embed.add_field(name="", value=f"I have been moved to {specified_vc.mention}. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.", inline=False)
                return await interaction.response.send_message(embed=move_user_embed)
            
            move_user_embed.add_field(name="", value=f"{member.mention} has been moved to {specified_vc.mention}.", inline=False)
            await interaction.response.send_message(embed=move_user_embed)

        else:
            await member.move_to(specified_vc, reason=reason)

            if interaction.user.id == self.bot.application_id:
                move_user_embed.add_field(name="", value=f"I have been moved to {specified_vc.mention} for **{reason}**. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.", inline=False)
                return await interaction.response.send_message(embed=move_user_embed)
            
            move_user_embed.add_field(name="", value=f"{member.mention} has been moved to {specified_vc.mention} for **{reason}**.", inline=False)
            await interaction.response.send_message(embed=move_user_embed)


    @move_user.error
    async def move_user_error(self, interaction: Interaction, error):
        move_user_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            move_user_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `move members` permission, and you probably **don't have** it, {interaction.user.mention}.", inline=False)
            await interaction.response.send_message(embed=move_user_error_embed)

        else:
            raise error


    # Moves the author to another specified voice channel
    @move.command(name="me", description="Moves you to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move you to.")
    @app_commands.describe(reason="Reason for move")
    async def move_me(self, interaction: Interaction, channel: discord.VoiceChannel, reason: Optional[str] = None):
        move_me_embed = discord.Embed(title="", color=interaction.user.color)
        move_me_error_embed = discord.Embed(title="", color=discord.Colour.red())

        # Check the target user was in the vc or not
        if interaction.user.voice is None:
            move_me_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> You're currently not in a voice channel!", inline=False)
            return await interaction.response.send_message(embed=move_me_error_embed)
        
        if reason is None:
            move_me_embed.add_field(name="", value=f"{interaction.user.mention} has been moved to {channel.mention}.", inline=False)
            await interaction.user.move_to(channel)
            await interaction.response.send_message(embed=move_me_embed)

        else:
            move_me_embed.add_field(name="", value=f"{interaction.user.mention} has been moved to {channel.mention} for **{reason}**.", inline=False)
            await interaction.user.move_to(channel, reason=reason)
            await interaction.response.send_message(embed=move_me_embed)


    @move_me.error
    async def move_me_error(self, interaction: Interaction, error):
        move_me_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            move_me_error_embed.add_field(name=f"<a:CrossRed:1274034371724312646> This command **requires** `move members` permission, and you probably **don't have** it, {interaction.user.mention}.", value="", inline=False)
            return await interaction.response.send_message(embed=move_me_error_embed)
        
        else:
            raise error
        

    # Moves the bot to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="bot", description="Moves me to another specified voice channel")
    @app_commands.checks.has_permissions(move_members=True, moderate_members=True)
    @app_commands.describe(channel="Channel to move me to. Leave this blank if you want to move me into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_bot(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)
        move_bot_embed = discord.Embed(title="", color=interaction.user.color)
        move_bot_error_embed = discord.Embed(title="", color=discord.Colour.red())

        # Check the bot was in the vc or not
        if player is None:
            move_bot_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I'm currently not in a voice channel.", inline=False)
            return await interaction.response.send_message(embed=move_bot_error_embed)
        
        if channel is None:

            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel

            else:
                # The author has not joined the voice channel yet
                move_bot_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like you're currently not in a voice channel, but trying to move me into the voice channel that you're connected :thinking: ...\nJust curious to know, where should I move into right now, {interaction.user.mention}?", inline=False)
                return await interaction.response.send_message(embed=move_bot_error_embed)
            
        else:
            specified_vc = channel

        if reason is None:
            move_bot_embed.add_field(name="", value=f"I have been moved to {specified_vc.mention}.", inline=False)
            await player.move_to(specified_vc)
            await interaction.response.send_message(embed=move_bot_embed)

        else:
            move_bot_embed.add_field(name="", value=f"I have been moved to {specified_vc.mention} for **{reason}**.", inline=False)
            await player.move_to(specified_vc)
            await interaction.response.send_message(embed=move_bot_embed)


    @move_bot.error
    async def move_bot_error(self, interaction: Interaction, error):
        move_bot_error_embed = discord.Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            move_bot_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `move members` and `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.", inline=False)
            return await interaction.response.send_message(embed=move_bot_error_embed)
        
        else:
            raise error

    # Convert time string to seconds and detailed duration breakdown
    def parse_duration(self, duration_str: str) -> Union[dict, str]:
        units = {
            "s": 1,        # seconds
            "m": 60,       # minutes
            "h": 3600,     # hours
            "d": 86400,    # days
            "w": 604800,   # weeks
            "mo": 2592000, # months (approximate)
            "y": 31536000  # years (approximate)
        }

        matches = re.findall(r"(\d+)(mo|[smhdwy])", duration_str)

        if not matches:
            return "error_improper_format"

        total_seconds = 0
        duration_breakdown = {
            "years": 0,
            "months": 0,
            "weeks": 0,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0
        }

        for amount, unit in matches:
            if unit in units:
                total_seconds += int(amount) * units[unit]
                duration_breakdown[{
                    "y": "years",
                    "mo": "months",
                    "w": "weeks",
                    "d": "days",
                    "h": "hours",
                    "m": "minutes",
                    "s": "seconds"
                }[unit]] += int(amount)

        duration_breakdown["total_seconds"] = total_seconds
        return duration_breakdown
    
    # Function of mutes a member from voice channel
    async def mute_member_voice(self, interaction: Interaction, member: discord.Member, duration_str: str | None, reason: str):
        vmute_embed = Embed(title="", color=interaction.user.color)
        vmute_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            if duration_str is not None:  # For time-based voice mute only
                total_duration = self.timestring_converter(duration_str)

                if total_duration == "error_improper_format":
                    vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like the time fomrmat you entered it's not vaild :thinking: ... Perhaps enter again and gave me a chance to handle it, {interaction.user.mention} :pleading_face:?", inline=False)
                    vmute_error_embed.add_field(name="Supported time format:", value=f"**1**s = **1** second | **2**m = **2** minutes | **5**h = **5** hours | **10**d = **10** days | **3**w = **3** weeks | **6**y = **6** years.", inline=False)
                    return await interaction.response.send_message(embed=vmute_error_embed)
                
            if member.voice.mute:
                vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **already muted from voice**!")
                return await interaction.response.send_message(embed=vmute_error_embed)
            
            duration_message = "for " + " and ".join(", ".join([f"**{value}** {unit[:-1]}" + ("s" if value > 1 else "") for unit, value in total_duration.items() if unit != "total_seconds" and value != 0]).rsplit(", ", 1)) + " " if duration_str is not None else ""
            reason_message =  f"\nReason: **{reason}**" if reason is not None else ""

            if reason is not None:
                await member.edit(mute=True, reason=reason)

            else:
                await member.edit(mute=True)

            vmute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted from voice** {duration_message}:zipper_mouth:{reason_message}")
            await interaction.response.send_message(embed=vmute_embed)

            if duration_str is not None:  # For time-based voice mute only
                await asyncio.sleep(total_duration["total_seconds"])

                if member.voice:
                    await member.edit(mute=False, reason=f"Automatically unmuted after {duration_str}.")
                    
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **mute that user from voice**. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=vmute_error_embed)

            else:
                raise e

    # Mutes a member from voice for a specified amount of time
    @app_commands.command(description="Mutes a member from voice channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to mute")
    @app_commands.describe(duration="Duration for mute (e.g. 1s = 1 second | 2m = 2 minutes | 5h = 5 hours | 10d = 10 days | 3w = 3 weeks | 6y = 6 years)")
    async def vmute(self, interaction: Interaction, member: discord.Member, duration: Optional[str] = None, reason: Optional[str] = None):
        vmute_error_embed = Embed(title="", color=discord.Colour.red())

        if member == interaction.user:
            vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, You can't **mute yourself from voice**!")
            return await interaction.response.send_message(embed=vmute_error_embed)
        
        if member.guild_permissions.administrator and interaction.user != interaction.guild.owner:

            if not await self.bot.is_owner(interaction.user):
                vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Stop trying to **mute an admin from voice**! :rolling_eyes:")
                return await interaction.response.send_message(embed=vmute_error_embed)
            
        if member == self.bot.user:
            vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **mute myself from voice**!")
            return await interaction.response.send_message(embed=vmute_error_embed)
        
        if member.voice is None:
            vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not connected to voice** currently.")
            return await interaction.response.send_message(embed=vmute_error_embed)
        
        await self.mute_member_voice(interaction, member, duration, reason)

    @vmute.error
    async def vmute_error(self, interaction: Interaction, error):
        vmute_error_embed = Embed(title="", color=discord.Colour.red())
        
        if isinstance(error, MissingPermissions):
            vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=vmute_error_embed)

        elif isinstance(error, BotMissingPermissions):
            vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **mute that user from voice**. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=vmute_error_embed)

        else:
            raise error

    # Unmutes a member from voice
    @app_commands.command(description="Unmutes a member from voice channels")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unmute (Enter the User ID e.g. 529872483195806124)")
    @app_commands.describe(reason="Reason for unmute")
    async def vunmute(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        vunmute_embed = Embed(title="", color=interaction.user.color)
        vunmute_error_embed = Embed(title="", color=discord.Colour.red())

        if member.voice is None:
            vunmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not connected to voice** currently.")
            return await interaction.response.send_message(embed=vunmute_error_embed)
        
        if not member.voice.mute:
            vunmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not muted from voice** currently.")
            return await interaction.response.send_message(embed=vunmute_error_embed)
        
        if reason is not None:
            await member.edit(mute=False, reason=reason)
            vunmute_embed.add_field(name="", value=f"{member.mention} has been **unmuted from voice**.\nReason: **{reason}**")

        else:
            await member.edit(mute=False)
            vunmute_embed.add_field(name="", value=f"{member.mention} has been **unmuted from voice**.")

        await interaction.response.send_message(embed=vunmute_embed)

    @vunmute.error
    async def vunmute_error(self, interaction: Interaction, error):
        vunmute_error_embed = Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            vunmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=vunmute_error_embed)

        elif isinstance(error, BotMissingPermissions):
            vunmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **unmute that user from voice**. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=vunmute_error_embed)

        else:
            raise error

    # Kicks a member from voice
    @app_commands.command(description="Kicks a member from the voice channel")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.checks.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="User to kick")
    @app_commands.rename(member="user")
    @app_commands.describe(reason="Reason for kick")
    async def vkick(self, interaction: Interaction, member: discord.Member, reason: Optional[str] = None):
        vkick_embed = Embed(title="", color=interaction.user.color)
        vkick_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            if member.voice is None:
                vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {member.mention} is **not in voice** currently.")
                return await interaction.response.send_message(embed=vkick_error_embed)
            
            if member == interaction.user:
                vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, You can't **kick yourself from voice**!")
                return await interaction.response.send_message(embed=vkick_error_embed)
            
            if member == self.bot.user:
                vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> {interaction.user.mention}, I can't **kick myself from voice**!")
                return await interaction.response.send_message(embed=vkick_error_embed)
            
            if member.guild_permissions.administrator and interaction.user != interaction.guild.owner:

                if not await self.bot.is_owner(interaction.user):
                    vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Stop trying to **kick an admin from voice**! :rolling_eyes:")
                    return await interaction.response.send_message(embed=vkick_error_embed)
                
            if reason is not None:
                await member.kick(reason=reason)
                vkick_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **kicked from voice**.\nReason: **{reason}**")

            else:
                await member.kick()
                vkick_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **kicked from voice**.")

            return await interaction.response.send_message(embed=vkick_embed)
        
        except Forbidden as e:
            if e.status == 403 and e.code == 50013:
                # Handling rare forbidden case
                vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **kick that user from voice**. Please **double-check** my **permissions** and **role position**.")
                await interaction.response.send_message(embed=vkick_error_embed)
                
            else:
                raise e
            
    @vkick.error
    async def vkick_error(self, interaction: Interaction, error):
        vkick_error_embed = Embed(title="", color=discord.Colour.red())

        if isinstance(error, MissingPermissions):
            vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> This command **requires** `moderate members` permission, and you probably **don't have** it, {interaction.user.mention}.")
            await interaction.response.send_message(embed=vkick_error_embed)

        elif isinstance(error, BotMissingPermissions):
            vkick_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> I couldn't **kick that user from voice**. Please **double-check** my **permissions** and **role position**.")
            await interaction.response.send_message(embed=vkick_error_embed)

        else:
            raise error


    # discord.py has no recording vc function.
    # 21102024 UPDATE: recording vc function can now be achieved by discord.ext.voice_recv plugin,
    # and has been separated as another cog (see VoiceRecorder.py)

    # ----------</Voice Channels>----------


async def setup(bot):
    await bot.add_cog(VoiceChannel(bot))
