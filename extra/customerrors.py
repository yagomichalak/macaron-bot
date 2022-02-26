from discord.ext import commands

class CommandNotReady(commands.CheckFailure):
    message = "Command is not ready!"

    def __str__(self) -> str:
        return self.message

class NotInGameTextChannelError(commands.CheckFailure):
    
    message = "You can only run this command in the bot's game Text Channel!"
    def __str__(self) -> str:
        return self.message
