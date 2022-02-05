import discord
from discord.ext import commands
from external_cons import the_database
from typing import Optional

class MacaronProfileTable(commands.Cog):
    """ Class for managing the MacaronProfile table. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_macaron_profile(self, ctx) -> None:
        """ Creates the MacaronProfile table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_macaron_profile_exists():
            return await ctx.send(f"**Table `MacaronProfile` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE MacaronProfile (
                user_id BIGINT NOT NULL,
                money BIGINT DEFAULT 0,
                games_played INT DEFAULT 0,
                last_time_played BIGINT DEFAULT NULL,
                PRIMARY KEY(user_id)
            )
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `MacaronProfile` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_macaron_profile(self, ctx) -> None:
        """ Dropss the MacaronProfile table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_macaron_profile_exists():
            return await ctx.send(f"**Table `MacaronProfile` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP MacaronProfile")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `MacaronProfile` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_macaron_profile(self, ctx) -> None:
        """ Resets the MacaronProfile table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_macaron_profile_exists():
            return await ctx.send(f"**Table `MacaronProfile` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM MacaronProfile")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `MacaronProfile` table, {member.mention}!**")


    async def check_table_macaron_profile_exists(self) -> bool:
        """ Checks whether the MacaronProfile table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'MacaronProfile'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_macaron_profile(self, user_id: int, money: int = 0, games_played: int = 0, last_time_played: int = None) -> None:
        """ Inserts a user into the MacaronProfile table.
        :param user_id: The ID of the user to insert.
        :param money: The initial amount of money.
        :param games_played: The initial amount of games played.
        :param last_time_played: The initial time for the last time the user played the game. """

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO MacaronProfile (
                user_id, money, games_played, last_time_played
            ) VALUES (%s, %s, %s, %s)
        """, (user_id, money, games_played, last_time_played))
        await db.commit()
        await mycursor.close()

    async def update_user_money(self, user_id: int, increment: Optional[int] = 0) -> None:
        """ Updates the user's money balance.
        :param user_id: The ID of the user to update.
        :param increment: The increment value. [Optional][Default = 0] """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE MacaronProfile SET money = money + %s WHERE user_id = %s", (increment, user_id))
        await db.commit()
        await mycursor.close()

    async def update_user_games_played(self, user_id: int, increment: Optional[int] = 0) -> None:
        """ Updates the user's games played counter.
        :param user_id: The ID of the user to update.
        :param increment: The increment value. [Optional][Default = 0] """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE MacaronProfile SET games_played = games_played + %s WHERE user_id = %s", (increment, user_id))
        await db.commit()
        await mycursor.close()

    async def update_user_last_time_played(self, user_id: int, current_ts: int) -> None:
        """ Updates the user's games played counter.
        :param user_id: The ID of the user to update.
        :param current_ts: The current timestamp. """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE MacaronProfile SET last_time_played = last_time_played + %s WHERE user_id = %s", (current_ts, user_id))
        await db.commit()
        await mycursor.close()

    async def update_user(self, user_id: int, 
        money: Optional[int] = None, games_played: Optional[int] = None, current_ts: Optional[int] = None) -> None:
        """ Updates the user status.
        :param user_id: The ID of the user to update.
        :param money: The increment value for the money field.
        :param games_played: The icnrement value for the games played field.
        :param current_ts: The current timestamp. """

        mycursor, db = await the_database()

        if money and games_played and current_ts:
            await mycursor.execute("""
                UPDATE MacaronProfile SET money = money + %s, games_played = games_played + %s,
                last_time_played = %s WHERE user_id = %s
                """, (money, games_played, current_ts, user_id))

        elif money and games_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET money = money + %s, 
                games_played = games_played + %s, WHERE user_id = %s
                """, (money, games_played, user_id))
        
        elif money and current_ts:
            await mycursor.execute("""
                UPDATE MacaronProfile SET money = money + %s, 
                last_time_played = %s, WHERE user_id = %s
                """, (money, current_ts, user_id))

        elif games_played and current_ts:
            await mycursor.execute("""
                UPDATE MacaronProfile SET games_played = games_played + %s, 
                last_time_played = %s, WHERE user_id = %s
                """, (money, games_played, user_id))

        await mycursor.execute("UPDATE MacaronProfile SET last_time_played = last_time_played + %s WHERE user_id = %s", (current_ts, user_id))
        await db.commit()
        await mycursor.close()

    async def delete_macaron_profile(self, user_id: int) -> None:
        """ Deletes a Macaron Profile.
        :param user_id: The ID of the user to delete. """

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM MacaronProfile WHERE user_id = %s", (user_id,))
        await db.commit()
        await mycursor.close()