import discord
from discord.ext import commands
from discord import Option, slash_command

from typing import List, Dict, Optional, Any, Union, Tuple, Callable
import os
import asyncio
import random
import shutil
import time

from external_cons import the_drive
from extra import utils
from extra.views import ReplayAudioView
from extra.game.game import GameSystem
from extra.game.macaron_profile import MacaronProfileTable
from extra.game.user_items import (
    RegisteredItemsTable, RegisteredItemsSystem, UserItemsTable, 
    UserItemsSystem, HiddenItemCategoryTable, ExclusiveItemRoleTable
)
from extra.game.audio_files import AudioFilesTable

server_id: int = int(os.getenv('SERVER_ID'))
guild_ids: List[int] = [server_id]

game_cogs: List[commands.Cog] = [
    MacaronProfileTable, RegisteredItemsTable, RegisteredItemsSystem,
    UserItemsTable, UserItemsSystem, HiddenItemCategoryTable,
    ExclusiveItemRoleTable, AudioFilesTable, GameSystem
]

class Game(*game_cogs):
    """ Category for the bot's main game. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client
        self.difficulty_modes: List[str] = ['A1', 'A2', 'B1', 'B2', 'C1-C2']
        self.player: discord.Member = None
        self.mode: str = None
        self.difficulty: str = None
        self.status: str = 'normal'
        self.txt: discord.TextChannel = None
        self.vc: discord.VoiceChannel = None
        self.audio_path: str = None
        self.reproduced_audios: List[str] = []
        self.round = 0
        self.lives: int = 3
        self.right_answers: int = 0
        self.wrong_answers: int = 0
        self.answer: discord.PartialMessageable = None
        self.session_id: str = None

        self.crumbs_emoji: str = '<:crumbs:940086555224211486>'
        self.croutons_emoji: str = '<:croutons:945013460041891891>'

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """ Tells when the cog is ready to go. """

        # Gets the game's main text channel
        guild = self.client.get_guild(server_id)
        self.txt = discord.utils.get(guild.text_channels, id=int(os.getenv('GAME_TEXT_CHANNEL_ID')))
        self.vc = discord.utils.get(guild.voice_channels, id=int(os.getenv('GAME_VOICE_CHANNEL_ID')))

        print('Game cog is ready!')

    @commands.command()
    @commands.is_owner()
    async def audio_update(self, ctx: Optional[commands.Context] = None, rall: str = 'no') -> None:
        """ Downloads all audios from the GoogleDrive and stores in the bot's folder.
        :param ctx: The context of the command. [Optional]
        :param rall: Whether the it should remove all folders before downloading files. """


        all_folders = {
            "Audio Files": "1IRQVO7kDXIVsbRnEoJbSNZSV0TRTYqYG",
            "SFX": "1lXLzALvyDo4eoyxzmXTeZWmlOU829F7r",
            }

        if rall.lower() == 'yes':
            for folder in all_folders:
                try:
                    shutil.rmtree(f'./resources/{folder}')
                except Exception:
                    pass

        categories = ['Audio Files', "SFX"]
        for category in categories:
            try:
                os.makedirs(f'./resources/{category}')
                print(f"{category} folder made!")
            except FileExistsError:
                pass

        drive = await the_drive()
        async with ctx.typing():
            for folder, folder_id in all_folders.items():

                await self.download_recursively(drive, 'resources', folder, folder_id)

        if ctx:
            await ctx.send("**Download audio update complete!**")

    @commands.command()
    @commands.is_owner()
    async def image_update(self, ctx: Optional[commands.Context] = None, rall: str = 'no') -> None:
        """ Downloads all shop images from the GoogleDrive and stores in the bot's folder.
        :param ctx: The context of the command. [Optional]
        :param rall: Whether the it should remove all folders before downloading files. """


        all_folders = {
            "accessories_1": "1Hd-79WiwtnQh-JYVI-y86DBozlmGrGab",
            "accessories_2": "18iplgiYltxCIi6sBaHgXrUKHSdXDN4sQ",
            "backgrounds": "1buwsKzDe1e6b4njfx9Nw-djGLyksnmJ8",
            "bb_base": "12NRW-ipOzXKU1HE4Z8RhbuCXEGDY-om5",
            "dual_hands": "1ItlzRT0gv65_izWBitT4SfR1r-drD2d4",
            "effects": "1pMlAE2nSGRc5Y-U2XIVg8c2WUv73Gv6E",
            "eyes": "1NcZwzltffgya5w9ijAWI8GyRAsX7LT47",
            "face_furniture": "1SpOSfiVpciWxztUZS3L_XmV28gf-w_33",
            "facial_hair": "1Bq-obguLHv5sIM4oBpMOmlGwOJWChF5n",
            "hats": "1kIKGvGFjoX5fwhQkvOKJ2AA4kgLFpMuo",
            "left_hands": "1ffFevrYq4FxPlEjIQ31fhqkIyTywr-41",
            "mouths": "1vcmsB7PI_a1s0jDxtHW9huYXv_5LWjYX",
            "right_hands": "1r4pga4OKpouQNKd95VWeO4FPCR7VzvsL",
            "outfits": "1RqRHtOfX-Vb6IHZgLJnEBn2AWBlrOypU",
            "pets": "1T0qG5YM6mGrgi9AsJab_apTDwI8VGAsb"
        }

        if rall.lower() == 'yes':
            for folder in all_folders:
                try:
                    shutil.rmtree(f'./resources/{folder}')
                except Exception:
                    pass

        categories = [
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 
            'dual_hands', 'effects', 'eyes', 'face_furniture', 
            'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands',
            'outfits', 'pets'
        ]
        for category in categories:
            try:
                os.makedirs(f'./resources/{category}')
                print(f"{category} folder made!")
            except FileExistsError:
                pass

        drive = await the_drive()
        async with ctx.typing():
            for folder, folder_id in all_folders.items():

                await self.download_recursively(drive, 'resources', folder, folder_id)

        if ctx:
            await ctx.send("**Download image update complete!**")

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
            'A1', 'A2', 'B1', 'B2', 'C1-C2'], required=False, default='A1')) -> None:
        """ Plays the game. """

        member: discord.Member = ctx.author
        await ctx.defer()

        if difficulty.upper() not in self.difficulty_modes:
            return await ctx.respond(f"**Please inform a valid mode, {member.mention}!\n`{', '.join(self.difficulty_modes)}`**")

        if self.player:
            return await ctx.respond(f"**There's already someone playing with the bot, {member.mention}!**")

        if not member.voice:
            return await ctx.respond(f"**You need to be in a Voice Channel to run this command, {member.mention}!**")

        if member.voice.channel.id != self.vc.id:
            return await ctx.respond(f"**You need to be in the {self.vc.mention} Voice Channel to play the game, {member.mention}!**")

        self.player = member
        self.difficulty = difficulty
        self.answer = ctx.respond
        self.session_id = self.generate_session_id()
        await self._play_command_callback()

    @commands.command(name="play")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _play_command(self, ctx, difficulty: str = 'A1') -> None:
        """ Plays the game.
        :param difficulty: The difficulty mode in which to play the game. [Default = A1] """

        member: discord.Member = ctx.author

        if difficulty.upper() not in self.difficulty_modes:
            return await ctx.send(f"**Please inform a valid mode, {member.mention}!\n`{', '.join(self.difficulty_modes)}`**")

        if self.player:
            return await ctx.send(f"**There's already someone playing with the bot, {member.mention}!**")
        
        if not member.voice:
            return await ctx.send(f"**You need to be in a Voice Channel to run this command, {member.mention}!**")

        if member.voice.channel.id != self.vc.id:
            return await ctx.send(f"**You need to be in the {self.vc.mention} Voice Channel to play the game, {member.mention}!**")

        self.player = member
        self.difficulty = difficulty.upper()
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
            # Gets reproduced files that are on cooldown
            current_ts = await utils.get_timestamp()
            raudio_files = await self.get_reproduced_audio_files(self.player.id, self.difficulty, current_ts)

            # Gets a random language audio
            path, difficulty_mode, audio_folder, fail = self.get_random_audio(raudio_files, current_ts)
            if fail:
                await self.txt.send(
                    embed=discord.Embed(
                        description=f"**We ran out of audios for you, come back in `24h`, {self.player.mention}!**",
                        color=discord.Color.orange()
                ))
                if self.right_answers >= 1:
                    crumbs = await self.reward_user()
                    await self.txt.send(f"""**
                    You've got `{crumbs}` crumbs {self.crumbs_emoji}!
                    ✅ `{self.right_answers}` | ❌ `{self.wrong_answers}`**""")
                return await self.stop_functionalities(self.player.guild)

            # Plays the song
            if not voice_client.is_playing():
                self.audio_path = f"{path}/audio.mp3"
                audio_source = discord.FFmpegPCMAudio(self.audio_path)
                text_source: str = await self.get_answer_text(f"{path}/answer.txt")
                dialect_source: str = await self.get_answer_text(f"{path}/dialect.txt")

                self.round += 1
                embed = discord.Embed(
                    title=f"__`ROUND {self.round}`__",
                    description="Try to understand what is being said in the following voice message, and type your answer below." \
                        f"\n**Language:** {dialect_source}" \
                        f"\n**Level:** {difficulty_mode}",
                    color=discord.Color.green()
                )
                await self.txt.send(embed=embed)
                if str(audio_folder) in list(map(lambda raf: raf[0], raudio_files)):
                    await self.update_audio_file(self.player.id, audio_folder, self.difficulty, current_ts)
                else:
                    await self.insert_audio_file(self.player.id, audio_folder, self.difficulty, current_ts)
                voice_client.play(audio_source, after=lambda e: self.client.loop.create_task(self.get_response(text_source)))

        else:
            # (to-do) send a message to a specific channel
            await self.txt.send("**The player left the voice channel, so it's game over!**")
            await self.reset_game_status()
        if self.round == 1:
            await self.answer(f"**Let's play, {self.player.mention}!**")

    async def reset_game_status(self) -> None:
        """ Clears the game status. """

        self.player = None
        self.mode = None
        self.difficulty = None
        self.status = 'normal'
        self.audio_path = None
        self.reproduced_audios = []
        self.round = 0
        self.lives = 3
        self.right_answers = 0
        self.wrong_answers = 0
        self.answer = None
        self.session_id = None
    
    async def stop_audio(self, guild: discord.Guild) -> None:
        """ Stops playing an audio.
        :param guild: The server. """

        voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=guild)
        if voice_client and voice_client.is_playing():
            self.status = 'stop'
            voice_client.stop()
        self.status = 'normal'

    def get_random_audio(self, raudio_files: List[str], current_ts: int) -> List[Union[str, bool, None]]:
        """ Gets a random audio.
        :param raudio_files: The reproduced audio files.
        :param current_ts: The current timestamp. """

        on_cooldown_audios = list(
            map(lambda oca: oca[0], 
                filter(lambda raf: current_ts - raf[1] <= 86400, raudio_files)
            )
        )

        root_path = './resources/Audio Files'

        difficulty: str = self.difficulty

        all_difficulties = os.listdir(root_path)
        all_audio_folders = os.listdir(f"{root_path}/{difficulty}")

        tries: int = 0
        laudios: int = len(all_difficulties)

        while True:
            tries += 1
            time.sleep(0.3)
            try:

                audio_folder = random.choice(all_audio_folders)
                all_audio_folders.remove(audio_folder)
                path = f"{root_path}/{difficulty}/{audio_folder}"

                # self.reproduced_audios.append(str(audio_folder))
                # return path, difficulty, audio_folder
                if not str(audio_folder) in self.reproduced_audios and str(audio_folder) not in on_cooldown_audios:
                    self.reproduced_audios.append(str(audio_folder))
                    return path, difficulty, audio_folder, False
                else:
                    continue
            except Exception:
                continue
            finally:
                if tries >= laudios:
                    return None, None, None, True

    async def get_response(self, text_source: str) -> Any:
        """ Checks how correct is the user's answer.
        :param text_source: The actual answer. """

        session_id: str = self.session_id

        if self.status == 'stop':
            self.status = 'normal'
            return

        if not self.player or self.session_id != session_id:
            return

        view = ReplayAudioView(self.client)
        await self.txt.send(
            embed=discord.Embed(
                description=f"🔰**`Answer!` ({self.player.mention})**🔰 ",
                color=discord.Color.green()),
            view=view
        )
            
        def check(m):
            if m.author.id == self.player.id and m.channel.id == self.txt.id:
                # Checks whether user is in the VC to answer the question

                return True

        answer: str = None

        try:
            answer = await self.client.wait_for('message', timeout=30, check=check)
        except asyncio.TimeoutError:
            try: view.stop()
            except: pass

            await self.stop_audio(self.vc.guild)
            await self.txt.send(f"**{self.player.mention}, you took too long to answer! (-1 ❤️)**")
            self.wrong_answers += 1
            self.lives -= 1
            await self.audio('resources/SFX/wrong_answer.mp3', self.vc)
        else:
            try: view.stop()
            except: pass

            await self.stop_audio(self.vc.guild)
            answer = answer.content
            if not answer:
                return

            accuracy = await self.compare_answers(answer, text_source)
            if accuracy >= 90:
                await self.txt.send(f"✅ You got it right, {self.player.mention}!\n**The answer was:** {text_source}")
                self.right_answers += 1
                await self.audio('resources/SFX/right_answer.mp3', self.vc)

            # Otherwise it's a wrong answer
            else:
                uanswer = self.highlight_answer(answer.split(), text_source.split())
                await self.txt.send(f"❌ You got it wrong, {self.player.mention}! ({accuracy}% accuracy)\n**Your answer:** {uanswer}\n**The answer was:** {text_source}")
                self.wrong_answers += 1
                self.lives -= 1
                await self.audio('resources/SFX/wrong_answer.mp3', self.vc)

        finally:
            if isinstance(answer, discord.Message):
                answer = answer.content

            current_ts = await utils.get_timestamp()
            # Checks if the member has remaining lives
            if answer and answer.startswith('mb!stop'):
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
                    You've got `{crumbs}` crumbs {self.crumbs_emoji}!
                    ✅ `{self.right_answers}` | ❌ `{self.wrong_answers}`**""")
                    await self.reset_game_status()
            else:
                await self.txt.send(f"**You lost the game, {self.player.mention}!** (0 ❤️)")
                await self.update_macaron_profile_crumbs(self.player.id, games_played=1, last_time_played=current_ts)
                await self.reset_game_status()

    async def get_answer_text(self, text_path: str) -> str:
        """ Gets the answer text.
        :param text_path: The path to the text file. """

        text_source: str = '?'
        try:
            with open(text_path, 'r', encoding="utf-8") as f:
                text_source: str = f.read()
        except:
            pass
        return text_source.strip()
    
    async def stop_functionalities(self, guild: discord.Guild) -> None:
        """ Stops the functionalities of the game.
        :param guild: The server. """

        await self.reset_game_status()
        await self.stop_audio(guild)

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        """ Stops the game. """

        author: discord.Member = ctx.author

        if not self.player:
            return await ctx.send(f"**{author.mention}, I'm not even playing yet!**")

        if self.player.id == author.id or await utils.is_allowed([]).predicate(ctx) or await utils.is_allowed_members([647452832852869120]).predicate(ctx):
            await self.stop_functionalities(ctx.guild)
            await ctx.send("**Session ended!**")
        else:
            return await ctx.send(f"{author.mention}, you're not the one who's playing, nor is a staff member")

    async def reward_user(self) -> int:
        """ Rewards the user. """

        current_ts = await utils.get_timestamp()
        player: discord.Member = self.player
        difficulty: str = self.difficulty

        multipliers: Dict[str, Tuple[int, int]] = {
            'A1': (1, 3), 'A2': (3, 5),
            'B1': (5, 8), 'B2':  (8, 10),
            'C1-C2': (10, 12),
        }

        money_to_add: int = 0

        m_range_x, m_range_y = multipliers.get(difficulty.upper())
        for _ in range(self.right_answers):
            money_to_add += random.randint(m_range_x, m_range_y)

        if await self.get_macaron_profile(player.id):
            await self.update_macaron_profile_crumbs(player.id, crumbs=money_to_add, games_played=1, last_time_played=current_ts)
        else:
            await self.insert_macaron_profile(player.id, crumbs=money_to_add, games_played=1, last_time_played=current_ts)

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
            description=f"**Crumbs:** {profile[1]} {self.crumbs_emoji}.\n" \
                f"**Croutons:** {profile[4]} {self.croutons_emoji}.\n" \
                f"**Games played:** {profile[2]}\n" \
                f"**Last time played:** {last_time_played}",
                color=member.color,
                timestamp=current_time
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.display_avatar)

        await answer(embed=embed)

    @slash_command(name="samples", guild_ids=guild_ids)
    async def _samples_slash_command(self, ctx: discord.ApplicationContext) -> None:
        """ Shows how many audio samples and languages we currently have in The Language Jungle game. """

        await ctx.defer()

        await self._samples_command_callback(ctx)

    @commands.command(name="samples", aliases=['audios', 'smpls', 'langs'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _samples_command(self, ctx: commands.Context) -> None:
        """ Shows how many audio samples and languages we currently have in The Language Jungle game. """

        await self._samples_command_callback(ctx)

    async def _samples_command_callback(self, ctx: Union[commands.Context, discord.ApplicationContext]) -> None:
        """ Shows how many audio samples we currently have in the game. (Callback) """

        answer: discord.PartialMessageable = None
        if isinstance(ctx, commands.Context):
            answer = ctx.send
        else:
            answer = ctx.respond

        path = './resources/Audio Files'
        difficulties = [folder for folder in os.listdir(path)]
        audios = [1 for difficulty in difficulties for _ in os.listdir(f"{path}/{difficulty}")]

        current_time = await utils.get_time_now()

        embed = discord.Embed(
            title="__Samples__",
            description=f"We currently have **`{sum(audios)}`** different audio samples grouped into **`{len(difficulties)}`** different difficulties respectively.",
            color=ctx.author.color,
            timestamp=current_time
        )
        embed.set_author(name=self.client.user, icon_url=self.client.user.display_avatar)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.display_avatar)
        await answer(embed=embed)

    async def audio(self, audio: str, channel: discord.VoiceChannel, func: Optional[Callable[[Any], Any]] = None) -> None:
        """ Reproduces an audio by informing a path and a channel.
        :param audio: The name of the audio.
        :param channel: The voice channel in which the bot will reproduce the audio in.
        :param func: What the bot will do after the audio is done. """

        voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=channel.guild)
        if not voice_client:
            await channel.connect()
            voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=channel.guild)

        if not voice_client.is_playing():
            audio_source = discord.FFmpegPCMAudio(audio)
            if not func:
                voice_client.play(audio_source)
            else:
                voice_client.play(audio_source, after=lambda e: self.client.loop.create_task(func()))


def setup(client: commands.Bot) -> None:
    """ Cog's setup function. """

    client.add_cog(Game(client))