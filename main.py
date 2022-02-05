import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
load_dotenv()

from extra.customerrors import CommandNotReady

client = commands.Bot(command_prefix='mb!')


@client.event
async def on_command_error(ctx, error) -> None:
    """ Command error handler. """

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("**You can't do that!**")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('**Please, inform all parameters!**')

    elif isinstance(error, commands.NotOwner):
        await ctx.send("**You're not the bot's owner!**")

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(error)

    elif isinstance(error, CommandNotReady):
        await ctx.respond(error)

    elif isinstance(error, commands.MissingAnyRole):
        role_names = [f"**{str(discord.utils.get(ctx.guild.roles, id=role_id))}**" for role_id in error.missing_roles]
        await ctx.send(f"You are missing at least one of the required roles: {', '.join(role_names)}")

    elif isinstance(error, commands.errors.RoleNotFound):
        await ctx.send(f"**Role not found**")

    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("**Channel not found!**")

    elif isinstance(error, commands.errors.CheckAnyFailure):
        await ctx.send("**You can't do that!**")


    print('=-'*20)
    print(f"ERROR: {error} | Class: {error.__class__} | Cause: {error.__cause__}")
    print('=-'*20)

    if error_log_channel := ctx.guild.get_channel(int(os.getenv('ERROR_CHANNEL_ID'))):
        await error_log_channel.send(error)

@client.event
async def on_application_command_error(ctx, error) -> None:
    """ Application command error handler. """

    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("**You can't do that!**")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.respond('**Please, inform all parameters!**')

    elif isinstance(error, commands.NotOwner):
        await ctx.respond("**You're not the bot's owner!**")

    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(error)

    elif isinstance(error, CommandNotReady):
        await ctx.respond(error)

    elif isinstance(error, commands.errors.CheckAnyFailure):
        await ctx.respond("**You can't do that!**")

    elif isinstance(error, commands.MissingAnyRole):
        role_names = [f"**{str(discord.utils.get(ctx.guild.roles, id=role_id))}**" for role_id in error.missing_roles]
        await ctx.respond(f"You are missing at least one of the required roles: {', '.join(role_names)}")

    elif isinstance(error, commands.errors.RoleNotFound):
        await ctx.respond(f"**Role not found**")

    elif isinstance(error, commands.ChannelNotFound):
        await ctx.respond("**Channel not found!**")

    elif isinstance(error, discord.app.commands.errors.CheckFailure):
        await ctx.respond("**It looks like you can't run this command!**")


    print('=-'*20)
    print(f"ERROR: {error} | Class: {error.__class__} | Cause: {error.__cause__}")
    print('=-'*20)

    if error_log_channel := ctx.guild.get_channel(int(os.getenv('ERROR_CHANNEL_ID'))):
        await error_log_channel.send(error)


@client.event
async def on_ready() -> None:
    """ Tells when the bot is ready to run. """

    print('Bot is online!')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f"cogs.{filename[:-3]}")

client.run(os.getenv('TOKEN'))