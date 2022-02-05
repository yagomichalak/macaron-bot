import discord
from discord.ext import commands, tasks
from discord import Option, OptionChoice, slash_command

from typing import List
import os

guild_ids: List[int] = [int(os.getenv('SERVER_ID'))]

class Game(commands.Cog):
    """ Category for the bot's main game. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client
        self.difficulty_modes: List[str] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        self.player = None
        self.mode = 'Idle'
        self.difficulty = None

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to go. """

        print('Game cog is ready!')

    @slash_command(name="play", guild_ids=guild_ids)
    async def _play_slash_command(self, ctx, 
        difficulty: Option(str, name="difficulty", description="The difficulty mode in which to play the game. [Default = A1]", choices=[
            'A1', 'A2', 'B1', 'B2', 'C1', 'C2'], required=False, default='A1')) -> None:
        """ Plays the game. """

        member: discord.Member = ctx.author
        await ctx.defer()

        if difficulty.upper() not in self.difficulty_modes:
            return await ctx.send(f"**Please inform a valid mode, {member.mention}!\n`{', '.join(self.difficulty_modes)}`**")

        await self._play_command_callback(ctx, member, difficulty)

    @commands.command(name="play")
    @commands.has_permissions(administrator=True)
    async def _play_command(self, ctx, difficulty: str = 'A1') -> None:
        """ Plays the game.
        :param difficulty: The difficulty mode in which to play the game. [Default = A1] """

        member: discord.Member = ctx.author

        if difficulty.upper() not in self.difficulty_modes:
            return await ctx.send(f"**Please inform a valid mode, {member.mention}!\n`{', '.join(self.difficulty_modes)}`**")

        await self._play_command_callback(ctx, member, difficulty)


    async def _play_command_callback(self, ctx, player: discord.Member, mode: str) -> None:
        """ Callback for the game's play command.
        :param player: The player of the game.
        :param difficulty: The difficulty mode. (A1-C2)"""

        answer: discord.PartialMessageable = ctx.send if isinstance(ctx, commands.Context) else ctx.respond

        await answer(f"**Let's play the game, {ctx.author.mention}!**")

    async def clear_game_status(self) -> None:
        """ Clears the game status. """

        self.player = None
        self.mode = 'Idle'
        self.difficulty = None


def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Game(client))