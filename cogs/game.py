import discord
from discord.ext import commands, tasks
from discord import Option, OptionChoice, slash_command

from typing import List
import os
import asyncio
import random

from fuzzywuzzy import fuzz

server_id: int = int(os.getenv('SERVER_ID'))
guild_ids: List[int] = [server_id]

class Game(commands.Cog):
    """ Category for the bot's main game. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client
        self.difficulty_modes: List[str] = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        self.player: discord.Member = None
        self.mode: str = None
        self.difficulty: str = None
        self.status: str = 'normal'
        self.txt: discord.TextChannel = None
        self.reproduced_audios: List[str] = []

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to go. """

        # Gets the game's main text channel
        guild = self.client.get_guild(server_id)
        self.txt = discord.utils.get(guild.text_channels, id=int(os.getenv('GAME_TEXT_CHANNEL_ID')))

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


    async def _play_command_callback(self, ctx, player: discord.Member, difficulty: str) -> None:
        """ Callback for the game's play command.
        :param player: The player of the game.
        :param difficulty: The difficulty mode. (A1-C2)"""

        answer: discord.PartialMessageable = ctx.send if isinstance(ctx, commands.Context) else ctx.respond

        server_bot: discord.Member = player.guild.get_member(self.client.user.id)
        if (bot_voice := server_bot.voice) and bot_voice.mute:
            await server_bot.edit(mute=False)
        
        voice = player.voice
        voice_client = player.guild.voice_client

        voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=player.guild)

        # Checks if the bot is in a voice channel
        if not voice_client:
            await voice.channel.connect()
            await asyncio.sleep(1)
            voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=player.guild)

        # Checks if the bot is in the same voice channel that the user
        if voice and voice.channel == voice_client.channel:
            # Gets a random language audio
            path, language, audio = self.get_random_audio(difficulty)
            # Plays the song
            if not voice_client.is_playing():
                audio_source = discord.FFmpegPCMAudio(path)

                self.round += 1
                embed = discord.Embed(
                    title=f"__`ROUND {self.round}`__",
                    description="The round starts now.",
                    color=discord.Color.green()
                )
                await self.txt.send(embed=embed)
                voice_client.play(audio_source, after=lambda e: self.client.loop.create_task(self.get_language_response(player, self.txt, language)))

        else:
            # (to-do) send a message to a specific channel
            await self.txt.send("**The player left the voice channel, so it's game over!**")
            await self.reset_bot_status()
        await answer(f"**Let's play the game, {ctx.author.mention}!**")

    async def clear_game_status(self) -> None:
        """ Clears the game status. """

        self.player = None
        self.mode = None
        self.difficulty = None
        self.status = 'normal'
        self.reproduced_audios = []

    async def compare_answers(self, player_answer: str, real_answer: str) -> int:
        """ Compares the player answer with the actual answer, and gives an
        accuracy percentage value.
        :param player: The player answer:
        :param real_answer: The real answer. """

        return fuzz.ratio(player_answer.lower(), real_answer.lower())

    def get_random_language(self, difficulty: str) -> str:
        """ Gets a random audio.
        :param difficulty: The difficulty mode for which to get the audio. """

        while True:
            try:
                path = './resources/audios'
                all_difficulties = os.listdir(path)
                difficulty_mode = random.choice(all_difficulties)
                all_audios = os.listdir(f"{path}/{difficulty_mode}")
                audio = random.choice(all_audios)
                path = f"{path}/{difficulty_mode}/{audio}"
                print('Audio: ', audio)
                if not str(audio) in self.reproduced_audios:
                    self.reproduced_audios.append(str(audio))
                    return path, difficulty_mode, audio
                else:
                    continue
            except Exception:
                print('try harder')
                continue

def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Game(client))