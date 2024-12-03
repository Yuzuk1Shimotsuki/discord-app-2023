import logging
from discord.ext import commands

def setup_logger(name, log_file, level=logging.INFO):
    """Function to set up a logger."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    
    return logger

# This is just a configuration for logging. No commands.Cog are involved.
class Logging(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Logging(bot))