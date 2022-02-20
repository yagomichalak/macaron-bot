import discord
from discord.ext import commands
from external_cons import the_database
from typing import List, Union


class AudioFilesTable(commands.Cog):
    """ Class for managing the AudioFiles table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_audio_files(self, ctx) -> None:
        """ Creates the AudioFiles table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_audio_files_exists():
            return await ctx.send(f"**Table `AudioFiles` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE AudioFiles (
                user_id BIGINT NOT NULL,
                file_name VARCHAR(100),
                difficulty ENUM('A1', 'A2', 'B1', 'B2', 'C1-C2'),
                audio_ts BIGINT NOT NULL,
                PRIMARY KEY(user_id, file_name, difficulty)
            )""")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `AudioFiles` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_audio_files(self, ctx) -> None:
        """ Dropss the AudioFiles table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_audio_files_exists():
            return await ctx.send(f"**Table `AudioFiles` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP AudioFiles")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `AudioFiles` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_audio_files(self, ctx) -> None:
        """ Resets the AudioFiles table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_audio_files_exists():
            return await ctx.send(f"**Table `AudioFiles` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM AudioFiles")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `AudioFiles` table, {member.mention}!**")


    async def check_table_audio_files_exists(self) -> bool:
        """ Checks whether the AudioFiles table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'AudioFiles'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_audio_file(self, user_id: int, file_name: str, difficulty: str, current_ts: int) -> None:
        """ Inserts an AudioFile into the database.
        :param user_id: The user ID.
        :param file_name: The file name.
        :param difficulty: The difficulty of the audio.
        :param current_ts: The current timestamp. """

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO AudioFiles (
                user_id, file_name, difficulty, audio_ts
            ) VALUES (%s, %s, %s, %s)
        """, (user_id, file_name, difficulty, current_ts))
        await db.commit()
        await mycursor.close()

    async def get_audio_file(self, user_id: int, file_name: str, difficulty: str) -> List[Union[int, str]]:
        """ Gets an AudioFile from a user from the database.
        :param user_id: The user ID.
        :param file_name: The file name.
        :param difficulty: The difficulty of the audio. """

        mycursor, _ = await the_database()
        await mycursor.execute("""
            SELECT * FROM AudioFiles WHERE user_id = %s AND file_name = %s AND difficulty = %s
            """, (user_id, file_name, difficulty))
        audio_file = await mycursor.fetchone()
        await mycursor.close()
        return audio_file

    async def get_audio_files(self, user_id: int, difficulty: str) -> List[List[Union[int, str]]]:
        """ Gets all AudioFile from a user from the database.
        :param user_id: The user ID.
        :param difficulty: The difficulty of the audio. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM AudioFiles WHERE user_id = %s AND difficulty = %s", (user_id, difficulty))
        audio_files = await mycursor.fetchall()
        await mycursor.close()
        return audio_files

    async def get_reproduced_audio_files(self, user_id: int, difficulty: str, current_ts: int) -> List[str]:
        """ Gets all reproduced audios from the user.
        :param user_id: The user ID.
        :param difficulty: The difficulty of the audios. """

        mycursor, _ = await the_database()
        await mycursor.execute("""
            SELECT file_name, audio_ts FROM AudioFiles WHERE user_id = %s AND difficulty = %s
        """, (user_id, difficulty))
        reproduced_audios = await mycursor.fetchall()
        await mycursor.close()
        return reproduced_audios

    async def update_audio_file(self, user_id: int, file_name: str, difficulty: str, current_ts: int) -> None:
        """ Updates an AudioFile's timestamp the database.
        :param user_id: The user ID.
        :param file_name: The file name.
        :param difficulty: The difficulty of the audio.
        :param current_ts: The new timestamp. """

        mycursor, db = await the_database()
        await mycursor.execute("""
            UPDATE AudioFiles SET audio_ts = %s
            WHERE user_id = %s AND file_name = %s AND difficulty = %s
        """, (current_ts, user_id, file_name, difficulty))
        await db.commit()
        await mycursor.close()