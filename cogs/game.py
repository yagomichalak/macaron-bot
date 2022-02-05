import discord
from discord.ext import commands
from discord import Option, slash_command

from typing import List, Optional, Any
import os
import asyncio
import random
import shutil
import time

from fuzzywuzzy import fuzz
from external_cons import the_drive

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
        self.round = 0

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to go. """

        # Gets the game's main text channel
        guild = self.client.get_guild(server_id)
        self.txt = discord.utils.get(guild.text_channels, id=int(os.getenv('GAME_TEXT_CHANNEL_ID')))

        print('Game cog is ready!')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def audio_update(self, ctx: Optional[commands.Context] = None, rall: str = 'no') -> None:
        """ Downloads all shop images from the GoogleDrive and stores in the bot's folder.
        :param ctx: The context of the command. [Optional]
        :param rall: Whether the it should remove all folders before downloading files. """

        if rall.lower() == 'yes':
            try:
                shutil.rmtree('./resources')
            except Exception:
                pass

        all_folders = {
            "audios": "1gyuXiVjB2shqgW4VRdqbJVldo9C0T79v",
        }
        categories = ['audios']
        for category in categories:
            try:
                os.makedirs(f'./resources/{category}')
                print(f"{category} folder made!")
            except FileExistsError:
                pass

        drive = await the_drive()

        for folder, folder_id in all_folders.items():

            await self.download_recursively(drive, 'resources', folder, folder_id)

        if ctx:
            await ctx.send("**Download update complete!**")

    async def download_recursively(self, drive, path: str, folder: str, folder_id: int) -> None:
        """ Downloads recursively through all folders and files form the GoogleDrive.
        :param drive: The drive connection object.
        :param path: The path to recurse.
        :param folder: The name of the folder of which you are recursing the files.
        :param folder_id: The ID of the folder. """

        files = drive.ListFile({'q': "'%s' in parents and trashed=false" % folder_id}).GetList()
        download_path = f'./{path}/{folder}'

        for file in files:
            try:
                #print(f"\033[34mItem name:\033[m \033[33m{file['title']:<35}\033[m | \033[34mID: \033[m\033[33m{file['id']}\033[m")
                output_file = os.path.join(download_path, file['title'])
                temp_file = drive.CreateFile({'id': file['id']})
                temp_file.GetContentFile(output_file)
                #print("File downloaded!")
            except Exception as error:
                new_category = file['title']
                try:
                    new_download_path = f"{download_path}/{new_category}"
                    os.makedirs(new_download_path)
                    print(f"{new_category} folder made!")
                except FileExistsError:
                    pass
                else:
                    await self.download_recursively(drive, download_path, new_category, file['id'])

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
            path, difficulty_mode, audio_folder = self.get_random_audio(difficulty)
            # Plays the song
            if not voice_client.is_playing():
                audio_source = discord.FFmpegPCMAudio(f"{path}/audio.mp3")
                text_source: str = await self.get_answer_text(f"{path}/answer.txt")

                self.round += 1
                embed = discord.Embed(
                    title=f"__`ROUND {self.round}`__",
                    description="The audio starts now.",
                    color=discord.Color.green()
                )
                await self.txt.send(embed=embed)
                voice_client.play(audio_source, after=lambda e: self.client.loop.create_task(self.get_response(player, text_source)))

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

    def get_random_audio(self, difficulty: str = None) -> str:
        """ Gets a random audio.
        :param difficulty: The difficulty mode for which to get the audio. """

        while True:
            time.sleep(0.3)
            try:
                path = './resources/audios'
                difficulty_mode: str = difficulty
                if not difficulty:
                    all_difficulties = os.listdir(path)
                    difficulty_mode = random.choice(all_difficulties)


                all_audio_folders = os.listdir(f"{path}/{difficulty_mode}")
                audio_folder = random.choice(all_audio_folders)
                path = f"{path}/{difficulty_mode}/{audio_folder}"
                if not str(audio_folder) in self.reproduced_audios:
                    self.reproduced_audios.append(str(audio_folder))
                    return path, difficulty_mode, audio_folder
                else:
                    continue
            except Exception:
                print('Try harder...')
                continue

    async def get_response(self, player: discord.Member, text_source: str) -> Any:
        """ Checks how correct is the user's answer.
        :param player: The player who answered.
        :param text_source: The actual answer. """

        if self.status == 'stop':
            self.status = 'normal'
            return

        await self.txt.send(f"🔰**`Answer!` ({player.mention})**🔰 ")
        def check(m):
            if m.author.id == player.id and m.channel.id == self.txt.id:
                # Checks whether user is in the VC to answer the question
                if m.content.startswith('mb!stop'):
                    self.client.loop.create_task(self.stop_round(player.guild))
                    return False

                return True

        try:
            answer = await self.client.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await self.txt.send(f"**{player.mention}, you took too long to answer! (-1 ❤️)")
            # self.wrong_answers += 1
            # self.lives -= 1
            # await self.audio('resources/SFX/wrong_answer.mp3', channel)
        else:
            answer = answer.content
            if not answer:
                return

            accuracy = await self.compare_answers(answer, text_source)
            if accuracy >= 75:
                await self.txt.send(f"🎉🍞 **You got it {accuracy}% `right`, {player.mention}! 🍞🎉\nThe answer was:** ```{text_source}```")
                # self.right_answers += 1
                # await self.audio('resources/SFX/right_answer.mp3', self.txt)

            # Otherwise it's a wrong answer
            else:
                await self.txt.send(f"❌ **You got it `wrong`, {player.mention}! ❌ (`{accuracy}% accuracy`)\nThe answer was:** ```{text_source}```")
                # self.wrong_answers += 1
                # self.lives -= 1
                # await self.audio('resources/SFX/wrong_answer.mp3', self.txt)


    async def get_answer_text(self, text_path: str) -> str:
        """ Gets the answer text.
        :param text_path: The path to the text file. """

        text_source: str = ''
        with open(text_path, 'r', encoding="utf-8") as f:
            text_source: str = f.read()

        return text_source

    async def stop_round(self) -> None: pass

def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Game(client))