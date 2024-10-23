import discord
from discord import Interaction
from discord.ext import commands

# Custom errors
class NotBotOwnerError:
    def __repr__(self) -> str:
        return f"Sorry, you have no permissions to perform this command.\n-# <:EyeNormal:1274033692356116522> This command is only permitted to bot owner, team owner, team admins & developers • [Learn more](<https://discord.com/developers/docs/topics/teams#team-member-roles>)"

class ExtensionNotFoundError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def __repr__(self) -> str:
        return f"I couldn't find the cog `{self.cog}` :pensive_face: ... Perhaps it was not a vaild input :thinking: ?"

class ReturnNoEntryPointError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def __repr__(self) -> str:
        return f"I couldn't find the `async def setup()` function in cog `{self.cog}` :pensive_face: ... Perhaps check the cog and try again :thinking: ?"

class ExtensionFailedError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def __repr__(self) -> str:
        return f"Some unexpected stuff happened while executing `{self.cog}`."
    
class InvaildTypeError():
    def __repr__(self) -> str:
        return "Looks like the type of message u provided it's not a valid type :thinking:..."
    
class MessageNotFoundError():
    def __repr__(self) -> str:
        return f'''I couldn't found the message from the given ID or URL :(
Have you entered a vaild ID or URL in the `message_id` field?'''

class AuthorNotInVoiceError():
    def __init__(self, interaction: Interaction, user: discord.User):
        self.interaction = interaction
        self.user = user
    def return_embed(self):
        embed = discord.Embed(title="", color=self.interaction.user.colour)
        embed.add_field(name="", value=f"{self.user.mention} Join a voice channel plz :pleading_face:  I don't think I can stay there without u :pensive: ...", inline=False)
        return embed

class BotAlreadyInVoiceError():
    def __init__(self, interaction: Interaction, bot_vc: discord.VoiceChannel, user_vc: discord.VoiceChannel):
        self.interaction = interaction
        self.bot_vc = bot_vc
        self.user_vc = user_vc
    def notauthor(self):
        notauthor_embed = discord.Embed(title="", color=self.interaction.user.colour)
        notauthor_embed.add_field(name="",value=f"I've already joined the voice channel :D , but not where you are ~\n\n**I'm currently in:** {self.bot_vc.mention}\n**You're currently in:** {self.user_vc.mention}")
        return notauthor_embed
    def notrequired(self):
        notrequired_embed = discord.Embed(title="", color=self.interaction.user.colour)
        notrequired_embed.add_field(name="",value=f"I've already joined the voice channel :D , but not the one you wanted me to join ~\n\n**I'm currently in:** {self.bot_vc.mention}\n**The channel you wanted me to join:** {self.user_vc.mention}")
        return notrequired_embed
    def same(self):
        same_embed = discord.Embed(title="", color=self.interaction.user.colour)
        same_embed.add_field(name="", value=f"Can you found me in the voice channel? I have connected to {self.user_vc.mention} already :>")
        return same_embed

class NotVaildEmojiError():
    def __repr__(self) -> str:
        return "It seems that the emoji you provided it's not a valid emoji :thinking:..."

# This is just a configuration for which error meesages are needed to return when error occurs. No commands.Cog are involved.
class ErrorHandling(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

async def setup(bot):
    await bot.add_cog(ErrorHandling(bot))