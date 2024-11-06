import discord
import asyncio
import re
import wavelink
from discord import app_commands, Embed, Interaction, Forbidden
from discord.ext import commands
from discord.app_commands import BotMissingPermissions
from discord.app_commands.errors import MissingPermissions
from typing import cast, Optional
from general.VoiceChannelFallbackConfig import *
from errorhandling.ErrorHandling import *

recording_vc = {}
    
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
        if player is not None:
            # Disconnect the bot from voice channel if it has been connected
            await player.disconnect()
            await interaction.response.send_message("Leaving...", ephemeral=True, delete_after=0)
        else:
            # The bot is currently not in a voice channel
            await interaction.response.send_message("I'm not in a voice channel ^_^.")

    # Moving all users or ends a voice call

    # Function to move all members (Can move them to any voice channel in the server, or use None to kick them away from the vc)
    async def move_all_members(self, interaction: Interaction, specified_vc, reason):
        moved_count = 0
        for member in interaction.guild.members:
            if member.voice is not None:
                if reason is None:
                    await member.move_to(specified_vc)
                else:
                    await member.move_to(specified_vc, reason=reason)
                moved_count += 1
        if moved_count == 0:
            return False
        return True
    
    # Ending a voice call
    @app_commands.command(name="end", description="End the call for all voice channels")
    @app_commands.checks.has_permissions(move_members=True)
    async def end(self, interaction: Interaction):
        await interaction.response.send_message("Ending the call for all voice channels...")
        if await self.move_all_members(interaction, None, None):
            await interaction.edit_original_response(content="Ended the call for all voice channels.")

    @end.error
    async def end_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to end the call!")
        else:
            raise error
    
    # Move all users to the voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="all", description="Moves all users to the specified voice channel")
    @app_commands.checks.has_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move them to. Leave this blank if you want to move them into where you are.")
    @app_commands.describe(reason="Reason for move")
    async def move_all(self, interaction: Interaction, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move all connected members into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move them all into right now, {interaction.user.mention}?''')
        else:
            specified_vc = channel
        await interaction.response.send_message(f"Moving all users to {specified_vc.mention}...")
        # Return True when successful to move, or return False when no users were found in the voice channel.
        if await self.move_all_members(interaction, specified_vc, reason=reason):
            if reason is None:
                await interaction.edit_original_response(content=f"All users has been moved to {specified_vc.mention}.")
            else:
                await interaction.edit_original_response(content=f"All users has been moved to {specified_vc.mention} for **{reason}**.")
        else:
            # No users were found in the voice channel
            await interaction.edit_original_response(content=f"No users were found in the voice channel.")


    @move_all.error
    async def move_all_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move all users!")
        else:
            raise error

    # Move an user to another voice channel which the author is already connected, or a specified voice channel.
    @move.command(name="user", description="Moves a member to another specified voice channel")
    @app_commands.describe(member="Member to move")
    @app_commands.describe(channel="Channel to move user to. Leave this blank if you want to move the user into where you are.")
    @app_commands.describe(reason="Reason for move")
    @commands.has_guild_permissions(move_members=True)
    async def move_user(self, interaction: Interaction, member: discord.Member, channel: Optional[discord.VoiceChannel] = None, reason: Optional[str] = None):
        # Check the target user was in the vc or not
        if member.voice is None and interaction.user.id == self.bot.application_id:
            return await interaction.response.send_message(f"I'm currently not in a voice channel.")
        elif interaction.user.voice is None:
            return await interaction.response.send_message(f"You're currently not in a voice channel !")
        elif member.voice is None:
            return await interaction.response.send_message(f"{member.mention} currently not in a voice channel.")
        # Check the target vc
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move someone into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move {member.mention} into right now, {interaction.user.mention}?''')
        else:
            specified_vc = channel
        if reason is None:
            await member.move_to(specified_vc)
            if interaction.user.id == self.bot.application_id:
                return await interaction.response.send_message(f"I have been moved to {specified_vc.mention}. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.")
            await interaction.response.send_message(f"{member.mention} has been moved to {specified_vc.mention}.")
        else:
            await member.move_to(specified_vc, reason=reason)
            if interaction.user.id == self.bot.application_id:
                return await interaction.response.send_message(f"I have been moved to {specified_vc.mention} for **{reason}**. You can also use </move bot:1212006756989800458> to move me into somewhere else next time :angel:.")
            await interaction.response.send_message(f"{member.mention} has been moved to {specified_vc.mention} for **{reason}**")

    @move_user.error
    async def move_user_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move users!")
        else:
            raise error

    # Moves the author to another specified voice channel
    @move.command(name="me", description="Moves you to another specified voice channel")
    @commands.has_guild_permissions(move_members=True)
    @app_commands.describe(channel="Channel to move you to.")
    @app_commands.describe(reason="Reason for move")
    async def move_me(self, interaction: Interaction, channel: discord.VoiceChannel, reason: Optional[str] = None):
        # Check the target user was in the vc or not
        if interaction.user.voice is None:
            return await interaction.response.send_message(f"You're currently not in a voice channel!")
        if reason is None:
            await interaction.user.move_to(channel)
            await interaction.response.send_message(f"{interaction.user.mention} has been moved to <#{channel.id}>.")
        else:
            await interaction.user.move_to(channel, reason=reason)
            await interaction.response.send_message(f"{interaction.user.mention} has been moved to <#{channel.id}> for {reason}")

    @move_me.error
    async def move_me_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move yourself!")
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
        # Check the bot was in the vc or not
        if player is None:
            return await interaction.response.send_message(f"I'm currently not in a voice channel.")
        if channel is None:
            if interaction.user.voice is not None:
                specified_vc = interaction.user.voice.channel
            else:
                # The author has not joined the voice channel yet
                return await interaction.response.send_message(f'''Looks like you're currently not in a voice channel, but trying to move me into the voice channel that you're connected :thinking: ...
Just curious to know, where should I move into right now, {interaction.user.mention}?''')
        else:
            specified_vc = channel
        if reason is None:
            await player.move_to(specified_vc)
            await interaction.response.send_message(f"I have been moved to {specified_vc.mention}.")
        else:
            await player.move_to(specified_vc, reason=reason)
            await interaction.response.send_message(f"I have been moved to {specified_vc.mention} for **{reason}**.")

    @move_bot.error
    async def move_bot_error(self, interaction: Interaction, error):
        if isinstance(error, MissingPermissions):
            await interaction.response.send_message("It seems that you don't have permission to move me!")
        else:
            raise error

    # Getting total seconds from timestring
    def timestring_converter(self, timestr):
        time_matches = re.findall(r"(\d+)(mo|[smhdwy])", timestr)
        if time_matches == []:
            return "error_improper_format"
        time_units = {
                    "s": 1,        # seconds
                    "m": 60,       # minutes
                    "h": 3600,     # hours
                    "d": 86400,    # days
                    "w": 604800,   # weeks
                    "mo": 2592000, # months (approximation)
                    "y": 31536000  # years (approximation)
                }
        # Calculate the total duration in seconds
        total_seconds = 0
        seconds = 0
        minutes = 0
        hours = 0
        days = 0
        weeks = 0
        months = 0
        years = 0
        for amount, unit in time_matches:
            if unit == "":
                return "error_improper_format"
            if unit == "s":
                seconds += int(amount)
            if unit == "m":
                minutes += int(amount)
            if unit == "h":
                hours += int(amount)
            if unit == "d":
                days += int(amount)
            if unit == "w":
                weeks += int(amount)
            if unit == "mo":
                months += int(amount)
            if unit == "y":
                years += int(amount)
            if unit in time_units:
                total_seconds += int(amount) * time_units[unit]
        return {"years": years, "months": months, "weeks": weeks, "days": days, "hours": hours, "minutes": minutes, "seconds": seconds, "total_seconds": total_seconds}
    
    # Function of mutes a member from voice channel
    async def mute_member_voice(self, interaction: Interaction, member, timestring, reason):
        vmute_embed = Embed(title="", color=interaction.user.color)
        vmute_error_embed = Embed(title="", color=discord.Colour.red())
        try:
            total_duration = self.timestring_converter(timestring)
            if total_duration == "error_improper_format":
                vmute_error_embed.add_field(name="", value=f"<a:CrossRed:1274034371724312646> Looks like the time fomrmat you entered it's not vaild :thinking: ... Perhaps enter again and gave me a chance to handle it, {interaction.user.mention} :pleading_face:?", inline=False)
                vmute_error_embed.add_field(name="Supported time format:", value=f"**1**s = **1** second | **2**m = **2** minutes | **5**h = **5** hours | **10**d = **10** days | **3**w = **3** weeks | **6**y = **6** years.", inline=False)
                return await interaction.response.send_message(embed=vmute_error_embed)
            if reason == None:
                await member.edit(mute=True, reason=reason)
                vmute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted from voice** for {'**' + str(total_duration["years"]) + '**' if total_duration["years"] != 0 else ''}{' year(s), ' if total_duration["years"] != 0 else ''}{'**' + str(total_duration["months"]) + '**' if total_duration["months"] != 0 else ''}{' month(s), ' if total_duration["months"] != 0 else ''}{'**' + str(total_duration["weeks"]) + '**' if total_duration["weeks"] != 0 else ''}{' week(s), ' if total_duration["weeks"] != 0 else ''}{'**' + str(total_duration["days"]) + '**' if total_duration["days"] != 0 else ''}{' day(s), ' if total_duration["days"] != 0 else ''}{'**' + str(total_duration["hours"]) + '**' if total_duration["hours"] != 0 else ''}{' hour(s), ' if total_duration["hours"] != 0 else ''}{'**' + str(total_duration["minutes"]) + '**' if total_duration["minutes"] != 0 else ''}{' minute(s), ' if total_duration["minutes"] != 0 else ''}{'**' + str(total_duration["seconds"]) + '**' if total_duration["seconds"] != 0 else ''}{' second(s). ' if total_duration["seconds"] != 0 else ''}:zipper_mouth:\nReason: **{reason}**")
            else:
                await member.edit(mute=True)
                vmute_embed.add_field(name="", value=f":white_check_mark: {member.mention} has been **muted from voice** for {'**' + str(total_duration["years"]) + '**' if total_duration["years"] != 0 else ''}{' year(s), ' if total_duration["years"] != 0 else ''}{'**' + str(total_duration["months"]) + '**' if total_duration["months"] != 0 else ''}{' month(s), ' if total_duration["months"] != 0 else ''}{'**' + str(total_duration["weeks"]) + '**' if total_duration["weeks"] != 0 else ''}{' week(s), ' if total_duration["weeks"] != 0 else ''}{'**' + str(total_duration["days"]) + '**' if total_duration["days"] != 0 else ''}{' day(s), ' if total_duration["days"] != 0 else ''}{'**' + str(total_duration["hours"]) + '**' if total_duration["hours"] != 0 else ''}{' hour(s), ' if total_duration["hours"] != 0 else ''}{'**' + str(total_duration["minutes"]) + '**' if total_duration["minutes"] != 0 else ''}{' minute(s), ' if total_duration["minutes"] != 0 else ''}{'**' + str(total_duration["seconds"]) + '**' if total_duration["seconds"] != 0 else ''}{' second(s). ' if total_duration["seconds"] != 0 else ''}:zipper_mouth:")
                await asyncio.sleep(total_duration["total_seconds"])
            await member.edit(mute=False)
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
    async def vmute(self, interaction: Interaction, member: discord.Member, duration: str, reason: Optional[str] = None):
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
