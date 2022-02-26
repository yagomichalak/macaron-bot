import discord
from discord.ext import commands, tasks
from discord.utils import escape_mentions
import os
from dotenv import load_dotenv
load_dotenv()

from extra.customerrors import CommandNotReady, NotInGameTextChannelError

client = commands.Bot(command_prefix='m!', intents=discord.Intents.all(), help_command=None, case_insensitive=True)


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
        await ctx.send(f"**{error}**")

    elif isinstance(error, NotInGameTextChannelError):
        await ctx.send(f"**{error}**")

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
        await ctx.respond(f"**{error}**")

    elif isinstance(error, NotInGameTextChannelError):
        await ctx.respond(f"**{error}**")

    elif isinstance(error, commands.errors.CheckAnyFailure):
        await ctx.respond("**You can't do that!**")

    elif isinstance(error, commands.MissingAnyRole):
        role_names = [f"**{str(discord.utils.get(ctx.guild.roles, id=role_id))}**" for role_id in error.missing_roles]
        await ctx.respond(f"You are missing at least one of the required roles: {', '.join(role_names)}")

    elif isinstance(error, commands.errors.RoleNotFound):
        await ctx.respond(f"**Role not found**")

    elif isinstance(error, commands.ChannelNotFound):
        await ctx.respond("**Channel not found!**")


    print('=-'*20)
    print(f"ERROR: {error} | Class: {error.__class__} | Cause: {error.__cause__}")
    print('=-'*20)

    if error_log_channel := ctx.guild.get_channel(int(os.getenv('ERROR_CHANNEL_ID'))):
        await error_log_channel.send(error)


@client.event
async def on_ready() -> None:
    """ Tells when the bot is ready to run. """

    print('Bot is online!')

@client.command()
async def help(ctx, *, cmd: str =  None):
    """ Shows some information about commands and categories. 
    :param cmd: The command/category. """


    if not cmd:
        embed = discord.Embed(
            title="All commands and categories",
            description=f"```ini\nUse {client.command_prefix}help command or {client.command_prefix}help category to know more about a specific command or category\n\n[Examples]\n[1] Category: {client.command_prefix}help Game\n[2] Command : {client.command_prefix}help character```",
            timestamp=ctx.message.created_at,
            color=ctx.author.color
            )

        for cog in client.cogs:
            cog = client.get_cog(cog)
            cog_commands = [c for c in cog.__cog_commands__ if hasattr(c, 'parent') and c.parent is None]
            commands = [f"{client.command_prefix}{c.name}" for c in cog_commands if hasattr(c, 'hidden') and not c.hidden]
            if commands:
                embed.add_field(
                    name=f"__{cog.qualified_name}__",
                    value=f"`Commands:` {', '.join(commands)}",
                    inline=False
                    )

        cmds = []
        for y in client.walk_commands():
            if not y.cog_name and hasattr(y, 'hidden') and not y.hidden:
                cmds.append(f"{client.command_prefix}{y.name}")

        embed.add_field(
            name='__Uncategorized Commands__',
            value=f"`Commands:` {', '.join(cmds)}",
            inline=False)
        await ctx.send(embed=embed)

    else:  
        cmd = escape_mentions(cmd)
        if command := client.get_command(cmd.lower()):
            command_embed = discord.Embed(title=f"__Command:__ {client.command_prefix}{command.qualified_name}", description=f"__**Description:**__\n```{command.help}```", color=ctx.author.color, timestamp=ctx.message.created_at)
            return await ctx.send(embed=command_embed)

        # Checks if it's a cog
        for cog in client.cogs:
            if str(cog).lower() == str(cmd).lower():
                cog = client.get_cog(cog)
                cog_embed = discord.Embed(title=f"__Cog:__ {cog.qualified_name}", description=f"__**Description:**__\n```{cog.description}```", color=ctx.author.color, timestamp=ctx.message.created_at)
                cog_commands = [c for c in cog.__cog_commands__ if hasattr(c, 'parent') and c.parent is None]
                for c in cog_commands:
                    if hasattr(c, 'hidden') and not c.hidden:
                        cog_embed.add_field(name=c.qualified_name, value=c.help, inline=False)

                return await ctx.send(embed=cog_embed)
        # Otherwise, it's an invalid parameter (Not found)
        else:
            await ctx.send(f"**Invalid parameter! It is neither a command nor a cog!**")


@client.command(hidden=True)
@commands.has_permissions(administrator=True)
async def load(ctx, extension: str = None):
    """ Loads a cog.
    :param extension: The cog. """

    if not extension:
        return await ctx.send("**Inform the cog!**")
    client.load_extension(f'cogs.{extension}')
    return await ctx.send(f"**{extension} loaded!**", delete_after=3)


@client.command(hidden=True)
@commands.has_permissions(administrator=True)
async def unload(ctx, extension: str = None):
    """ Unloads a cog.
    :param extension: The cog. """

    if not extension:
        return await ctx.send("**Inform the cog!**")
    client.unload_extension(f'cogs.{extension}')
    return await ctx.send(f"**{extension} unloaded!**", delete_after=3)


@client.command(hidden=True)
@commands.has_permissions(administrator=True)
async def reload(ctx, extension: str = None):
    """ Reloads a cog.
    :param extension: The cog. """

    if not extension:
        return await ctx.send("**Inform the cog!**")
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    return await ctx.send(f"**{extension} reloaded!**", delete_after=3)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f"cogs.{filename[:-3]}")

client.run(os.getenv('TOKEN'))