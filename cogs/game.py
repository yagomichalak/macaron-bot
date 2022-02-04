import discord
from discord.ext import commands, tasks

class Game(commands.Cog):
    """ Category for the bot's main game. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to go. """

        print('Game cog is ready!')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def play(self, ctx) -> None:
        """ Plays the game. """

        await ctx.send(f"**Let's play the game, {ctx.author.mention}!**")


def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Game(client))