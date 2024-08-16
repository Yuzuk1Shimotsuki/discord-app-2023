import discord
from discord import app_commands, Interaction
from discord.ext import commands

# Custom errors
class NotBotOwnerError:
    def __repr__(self) -> str:
        return f"Sorry, you have no permission to perform this command.\n-# <:eye2:1273644542926651485> This command is only permitted to bot owner, team owner, team admins & developers • [Learn more](<https://discord.com/developers/docs/topics/teams#team-member-roles>)"

class ExtensionNotFoundError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def __repr__(self) -> str:
        return f"I couldn't find the cog `{self.cog}` :pensive_face: ... Perhaps it was not a vaild input :thinking: ？"

class ReturnNoEntryPointError:
    def __init__(self, cog: str) -> None:
        self.cog = cog

    def __repr__(self) -> str:
        return f"I couldn't find the `async def setup()` function in cog `{self.cog}` :pensive_face: ... Perhaps check the cog and try again :thinking: ？"

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
Have you entered a vaild ID or URL in the `message_id` field？'''

class AuthorNotInVoiceError():
    def __init__(self, interaction: Interaction, user: discord.User):
        self.user = user
        self.interaction = interaction
    def return_embed(self):
        embed = discord.Embed(title="", color=self.interaction.user.colour)
        embed.add_field(name="", value=f"<@{self.user.id}> Join a voice channel plz :pleading_face:  I don't think I can stay there without u :pensive: ...", inline=False)
        return embed

class BotAlreadyInVoiceError():
    def __init__(self, bot_vc, user_vc):
        self.bot_vc = bot_vc
        self.user_vc = user_vc
    def notauthor(self):
        return f'''I've already joined the voice channel :D , but not where you are ~
**I'm currently in:** <#{self.bot_vc.id}>
**You're currently in:** <#{self.user_vc.id}>'''
    def notrequired(self):
        return f'''I've already joined the voice channel :D , but not the one you wanted me to join ~
**I'm currently in:** <#{self.bot_vc.id}>
**The channel you wanted me to join:** <#{self.user_vc.id}>'''
    def same(self):
        return f"Can u found me in the voice channel？ I have connected to  <#{self.user_vc.id}> already :>"
    
    