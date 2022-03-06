import discord
from discord.ext import commands
from discord.utils import escape_mentions

import inspect
import io
import textwrap
import traceback
from contextlib import redirect_stdout
from typing import List

from extra.tools.scheduled_events import ScheduledEventsTable, ScheduledEventsSystem

tool_cogs: List[commands.Cog] = [
    ScheduledEventsTable, ScheduledEventsSystem
]


class Tools(*tool_cogs):
    """ Category for tool commands. """

    def __init__(self, client: commands.Cog) -> None:
        """ Class init method. """

        self.client = client
        self.give_monthly_crumbs.start()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to go. """

        print('Tools cog is ready!')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def eval(self, ctx, *, body=None):
        """ (ADM) Executes a given command from Python onto Discord.
        :param body: The body of the command. """
        await ctx.message.delete()
        if not body:
            return await ctx.send("**Please, inform the code body!**")

        """Evaluates python code"""
        env = {
            'ctx': ctx,
            'client': self.client,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'source': inspect.getsource
        }

        def cleanup_code(content):
            """Automatically removes code blocks from the code."""
            # remove ```py\n```
            if content.startswith('```') and content.endswith('```'):
                return '\n'.join(content.split('\n')[1:-1])

            # remove `foo`
            return content.strip('` \n')

        def get_syntax_error(e):
            if e.text is None:
                return f'```py\n{e.__class__.__name__}: {e}\n```'
            return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

        env.update(globals())

        body = cleanup_code(body)
        stdout = io.StringIO()
        err = out = None

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        def paginate(text: str):
            '''Simple generator that paginates text.'''
            last = 0
            pages = []
            for curr in range(0, len(text)):
                if curr % 1980 == 0:
                    pages.append(text[last:curr])
                    last = curr
                    appd_index = curr
            if appd_index != len(text) - 1:
                pages.append(text[last:curr])
            return list(filter(lambda a: a != '', pages))

        try:
            exec(to_compile, env)
        except Exception as e:
            err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
            return await ctx.message.add_reaction('\u2049')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    try:

                        out = await ctx.send(f'```py\n{value}\n```')
                    except:
                        paginated_text = paginate(value)
                        for page in paginated_text:
                            if page == paginated_text[-1]:
                                out = await ctx.send(f'```py\n{page}\n```')
                                break
                            await ctx.send(f'```py\n{page}\n```')
            else:
                try:
                    out = await ctx.send(f'```py\n{value}{ret}\n```')
                except:
                    paginated_text = paginate(f"{value}{ret}")
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            out = await ctx.send(f'```py\n{page}\n```')
                            break
                        await ctx.send(f'```py\n{page}\n```')

        if out:
            await ctx.message.add_reaction('\u2705')  # tick
        elif err:
            await ctx.message.add_reaction('\u2049')  # x
        else:
            await ctx.message.add_reaction('\u2705')

    @commands.command()
    async def ping(self, ctx):
        """ Show the latency. """

        await ctx.send(f"**:ping_pong: Pong! {round(self.client.latency * 1000)}ms.**")

    @commands.command(aliases=['al', 'alias'])
    async def aliases(self, ctx, *, cmd: str = None):
        """ Shows some information about commands and categories. 
        :param cmd: The command. """

        if not cmd:
            return await ctx.send("**Please, informe one command!**")

        cmd = escape_mentions(cmd)
        if command := self.client.get_command(cmd.lower()):
            embed = discord.Embed(title=f"Command: {command}", color=ctx.author.color, timestamp=ctx.message.created_at)
            aliases = [alias for alias in command.aliases]

            if not aliases:
                return await ctx.send("**This command doesn't have any aliases!**")
            embed.description = '**Aliases: **' + ', '.join(aliases)
            return await ctx.send(embed=embed)
        else:
            await ctx.send(f"**Invalid parameter! It is neither a command nor a cog!**")


def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Tools(client))
