import discord
from discord.ext import commands
from discord import Option, slash_command

from typing import List, Dict, Optional, Any
import os
import asyncio
import random
import shutil
import time
import string

from fuzzywuzzy import fuzz
from external_cons import the_drive
from extra import utils
from extra.game.macaron_profile import MacaronProfileTable

server_id: int = int(os.getenv('SERVER_ID'))
guild_ids: List[int] = [server_id]

game_cogs: List[commands.Cog] = [
    MacaronProfileTable
]

class Game(*game_cogs):
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
        self.lives: int = 3
        self.right_answers: int = 0
        self.wrong_answers: int = 0
        self.answer: discord.PartialMessageable = None
        self.session_id: str = None

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
            "Audio Files": "1IRQVO7kDXIVsbRnEoJbSNZSV0TRTYqYG",
        }
        categories = ['Audio Files']
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

        if self.player:
            return await ctx.respond(f"**There's already someone playing with the bot, {member.mention}!**")

        self.player = member
        self.difficulty = difficulty
        self.answer = ctx.respond
        self.session_id = self.generate_session_id()
        await self._play_command_callback()

    @commands.command(name="play")
    @commands.has_permissions(administrator=True)
    async def _play_command(self, ctx, difficulty: str = 'A1') -> None:
        """ Plays the game.
        :param difficulty: The difficulty mode in which to play the game. [Default = A1] """

        member: discord.Member = ctx.author

        if difficulty.upper() not in self.difficulty_modes:
            return await ctx.send(f"**Please inform a valid mode, {member.mention}!\n`{', '.join(self.difficulty_modes)}`**")

        if self.player:
            return await ctx.send(f"**There's already someone playing with the bot, {member.mention}!**")

        self.player = member
        self.difficulty = difficulty
        self.answer = ctx.send
        self.session_id = self.generate_session_id()
        await self._play_command_callback()


    async def _play_command_callback(self) -> None:
        """ Callback for the game's play command. """

        server_bot: discord.Member = self.player.guild.get_member(self.client.user.id)
        if (bot_voice := server_bot.voice) and bot_voice.mute:
            await server_bot.edit(mute=False)
        
        voice = self.player.voice
        voice_client = self.player.guild.voice_client

        voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=self.player.guild)

        # Checks if the bot is in a voice channel
        if not voice_client:
            await voice.channel.connect()
            await asyncio.sleep(1)
            voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=self.player.guild)

        # Checks if the bot is in the same voice channel that the user
        if voice and voice.channel == voice_client.channel:
            # Gets a random language audio
            path, difficulty_mode, audio_folder = self.get_random_audio(self.difficulty)
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
                voice_client.play(audio_source, after=lambda e: self.client.loop.create_task(self.get_response(text_source)))

        else:
            # (to-do) send a message to a specific channel
            await self.txt.send("**The player left the voice channel, so it's game over!**")
            await self.reset_game_status()
        await self.answer(f"**Let's play the game, {self.player.mention}!**")

    async def reset_game_status(self) -> None:
        """ Clears the game status. """

        self.player = None
        self.mode = None
        self.difficulty = None
        self.status = 'normal'
        self.reproduced_audios = []
        self.round = 0
        self.lives = 3
        self.right_answers = 0
        self.wrong_answers = 0
        self.answer = None
        self.session_id = None

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
                path = './resources/Audio Files'
                difficulty_mode: str = difficulty
                if not difficulty:
                    all_difficulties = os.listdir(path)
                    difficulty_mode = random.choice(all_difficulties)


                all_audio_folders = os.listdir(f"{path}/{difficulty_mode}")
                audio_folder = random.choice(all_audio_folders)
                path = f"{path}/{difficulty_mode}/{audio_folder}"

                self.reproduced_audios.append(str(audio_folder))
                return path, difficulty_mode, audio_folder
                # if not str(audio_folder) in self.reproduced_audios:
                #     self.reproduced_audios.append(str(audio_folder))
                #     return path, difficulty_mode, audio_folder
                # else:
                #     continue
            except Exception:
                print('Try harder...')
                continue

    async def get_response(self, text_source: str) -> Any:
        """ Checks how correct is the user's answer.
        :param text_source: The actual answer. """

        session_id: str = self.session_id

        if self.status == 'stop':
            self.status = 'normal'
            return

        if not self.player or self.session_id != session_id:
            return

        await self.txt.send(f"🔰**`Answer!` ({self.player.mention})**🔰 ")
            
        def check(m):
            if m.author.id == self.player.id and m.channel.id == self.txt.id:
                # Checks whether user is in the VC to answer the question

                return True

        try:
            answer = await self.client.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            await self.txt.send(f"**{self.player.mention}, you took too long to answer! (-1 ❤️)")
            self.wrong_answers += 1
            self.lives -= 1
            # await self.audio('resources/SFX/wrong_answer.mp3', channel)
        else:
            answer = answer.content
            if not answer:
                return

            accuracy = await self.compare_answers(answer, text_source)
            if accuracy >= 90:
                await self.txt.send(f"🎉🍞 **You got it {accuracy}% `right`, {self.player.mention}! 🍞🎉\nThe answer was:** ```{text_source}```")
                self.right_answers += 1
                # await self.audio('resources/SFX/right_answer.mp3', self.txt)

            # Otherwise it's a wrong answer
            else:
                await self.txt.send(f"❌ **You got it `wrong`, {self.player.mention}! ❌ (`{accuracy}% accuracy`)\nThe answer was:** ```{text_source}```")
                self.wrong_answers += 1
                self.lives -= 1
                # await self.audio('resources/SFX/wrong_answer.mp3', self.txt)

        finally:
            # Checks if the member has remaining lives
            if answer.startswith('mb!stop'):
                return
                
            if self.lives > 0:				
                # Restarts the game if it's not the last round
                if self.round < 10:
                    await self.txt.send(f"**New round in 10 seconds...**")
                    await asyncio.sleep(10)
                    if self.player and self.session_id == session_id:
                        return await self._play_command_callback()
                
                # Otherwise it ends the game and shows the score of the member
                else:
                    #self.reproduced_languages = []
                    await self.txt.send(f"💪 **End of the game, you did it, {self.player.mention}!** 💪")
                    crumbs = await self.reward_user()
                    await self.txt.send(f"""**
                    You've got `{crumbs}` crumbs!
                    ✅ `{self.right_answers}` | ❌ `{self.wrong_answers}`**""")
                    await self.reset_game_status()

    async def get_answer_text(self, text_path: str) -> str:
        """ Gets the answer text.
        :param text_path: The path to the text file. """

        text_source: str = ''
        with open(text_path, 'r', encoding="utf-8") as f:
            text_source: str = f.read()

        return text_source.strip()

    def generate_session_id(self, length: Optional[int] = 18) -> str:
        """ Generates a session ID.
        :param length: The length of the session ID. [Default = 18] """

        # Defines data
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        num = string.digits
        symbols = string.punctuation

        # Combines the data
        all = lower + upper + num + symbols

        # Uses random 
        temp = random.sample(all,length)

        # Create the session ID 
        session_id = "".join(temp)
        return session_id


    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        """ Stops the game. """

        author: discord.Member = ctx.author

        if not self.player:
            return await ctx.send(f"**{author.mention}, I'm not even playing yet!**")

        if self.player.id == author.id or await utils.is_allowed([]).predicate(ctx) or await utils.is_allowed_members([647452832852869120]).predicate(ctx):
            await self.reset_game_status()
            guild = ctx.message.guild
            voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=guild)
            if voice_client and voice_client.is_playing():
                self.status = 'stop'
                voice_client.stop()

            self.status = 'normal'
            await ctx.send("**Session ended!**")
        else:
            return await ctx.send(f"{author.mention}, you're not the one who's playing, nor is a staff member")

    async def reward_user(self) -> int:
        """ Rewards the user. """

        current_ts = await utils.get_timestamp()
        player: discord.Member = self.player
        right_answers: int = self.right_answers
        difficulty: str = self.difficulty

        multipliers: Dict[str, int] = {
            'A1': 1, 'A2': 3,
            'B1': 5, 'B2':  10,
            'C1': 15, 'C2': 20,
        }

        selected_multiplier = multipliers.get(difficulty.upper())
        money_to_add: int = right_answers * selected_multiplier

        if await self.get_macaron_profile(player.id):
            await self.update_macaron_profile(player.id, money=money_to_add, games_played=1, last_time_played=current_ts)
        else:
            await self.insert_macaron_profile(player.id, money=money_to_add, games_played=1, last_time_played=current_ts)

        return money_to_add

    @slash_command(name="profile", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _profile_slash_command(self, ctx,
        member: Option(discord.Member, name="member", description="The member to check.", required=False)) -> None:
        """ Checks someone's profile. """

        if not member:
            member = ctx.author
        
        await ctx.defer()
        await self._profile_command_callback(ctx, member)

    @commands.command(name="profile")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _profile_command(self, ctx, member: Optional[discord.Member] = None) -> None:
        """ Checks someone's profile.
        :param member: The member to check. [Optional][Default = You] """

        if not member:
            member = ctx.author

        await self._profile_command_callback(ctx, member)

    async def _profile_command_callback(self, ctx, member: Optional[discord.Member]) -> None:
        """ Callback for the profile command.
        :param member: The member to check the profile. """

        answer: discord.PartialMessageable = ctx.reply if isinstance(ctx, commands.Context) else ctx.respond
        if member.bot:
            return await answer("**You cannot use this on a bot!**")

        if not (profile := await self.get_macaron_profile(member.id)):
            if ctx.author.id != member.id:
                return await answer("**This user doesn't have a profile!**")
            await self.insert_macaron_profile(member.id)
            profile = await self.get_macaron_profile(member.id)

        last_time_played: str = 'Never' if not profile[3] else f"<t:{profile[3]}:R>"
        current_time = await utils.get_time_now()

        embed: discord.Embed = discord.Embed(
            title=f"{member}'s Profile",
            description=f"**Money:** {profile[1]} crumbs.\n" \
                f"**Games played:** {profile[2]}\n" \
                f"**Last time played:** {last_time_played}",
                color=member.color,
                timestamp=current_time
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.display_avatar)

        await answer(embed=embed)

def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Game(client))