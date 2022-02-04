import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
load_dotenv()

client = commands.Bot(command_prefix='mb!')

@client.event
async def on_ready() -> None:
    """ Tells when the bot is ready to run. """

    print('Bot is online!')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f"cogs.{filename[:-3]}")

client.run(os.getenv('TOKEN'))