import discord
from discord.ext import commands
from external_cons import the_database
from typing import Optional, List, Union, Tuple

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
                croutons BIGINT DEFAULT 0,
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

    async def insert_macaron_profile(self, user_id: int, crumbs: int = 0, games_played: int = 0, last_time_played: int = None, croutons: int = 0) -> None:
        """ Inserts a user into the MacaronProfile table.
        :param user_id: The ID of the user to insert.
        :param crumbs: The initial amount of money. (crumbs)
        :param games_played: The initial amount of games played.
        :param last_time_played: The initial time for the last time the user played the game.
        :param croutons: The initial amount of money. (croutons) """

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO MacaronProfile (
                user_id, money, games_played, last_time_played, croutons
            ) VALUES (%s, %s, %s, %s, %s)
        """, (user_id, crumbs, games_played, last_time_played, croutons))
        await db.commit()
        await mycursor.close()

    async def get_macaron_profile(self, user_id: int) -> List[Union[str, int]]:
        """ Gets a Macaron Profile.
        :param user_id: The ID of the user to get. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM MacaronProfile WHERE user_id = %s", (user_id,))
        profile = await mycursor.fetchone()
        await mycursor.close()
        return profile

    async def update_user_crumbs(self, user_id: int, increment: Optional[int] = 0) -> None:
        """ Updates the user's money balance. (crumbs)
        :param user_id: The ID of the user to update.
        :param increment: The increment value. [Optional][Default = 0] """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE MacaronProfile SET money = money + %s WHERE user_id = %s", (increment, user_id))
        await db.commit()
        await mycursor.close()

    async def bulk_update_user_crumbs(self, users: List[Tuple[int, int]]) -> None:
        """ Bulk updates the users' money balance. (crumbs)
        :param users: The users to update """

        mycursor, db = await the_database()
        await mycursor.executemany("""
            UPDATE MacaronProfile SET money = money + %s WHERE user_id = %s
            """, users)
        await db.commit()
        await mycursor.close()

    async def bulk_update_user_croutons(self, users) -> None:
        """ Bulk updates the users' money balance. (croutons)
        :param users: The users to update """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE MacaronProfile SET croutons = croutons + %s WHERE user_id = %s", users)
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

    async def update_macaron_profile_crumbs(self, user_id: int, 
        crumbs: Optional[int] = None, games_played: Optional[int] = None, last_time_played: Optional[int] = None) -> None:
        """ Updates the user status.
        :param user_id: The ID of the user to update.
        :param crumbs: The increment value for the money field. (crumbs)
        :param games_played: The icnrement value for the games played field.
        :param last_time_played: The current timestamp. """

        mycursor, db = await the_database()

        if crumbs and games_played and last_time_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET money = money + %s, games_played = games_played + %s,
                last_time_played = %s WHERE user_id = %s
                """, (crumbs, games_played, last_time_played, user_id))

        elif crumbs and games_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET money = money + %s, 
                games_played = games_played + %s WHERE user_id = %s
                """, (crumbs, games_played, user_id))
        
        elif crumbs and last_time_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET money = money + %s, 
                last_time_played = %s WHERE user_id = %s
                """, (crumbs, last_time_played, user_id))

        elif games_played and last_time_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET games_played = games_played + %s, 
                last_time_played = %s WHERE user_id = %s
                """, (games_played, last_time_played, user_id))

        await db.commit()
        await mycursor.close()

    async def update_macaron_profile_croutons(self, user_id: int, 
        croutons: Optional[int] = None, games_played: Optional[int] = None, last_time_played: Optional[int] = None) -> None:
        """ Updates the user status.
        :param user_id: The ID of the user to update.
        :param croutons: The increment value for the money field. (croutons)
        :param games_played: The icnrement value for the games played field.
        :param last_time_played: The current timestamp. """

        mycursor, db = await the_database()

        if croutons and games_played and last_time_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET croutons = croutons + %s, games_played = games_played + %s,
                last_time_played = %s WHERE user_id = %s
                """, (croutons, games_played, last_time_played, user_id))

        elif croutons and games_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET croutons = croutons + %s, 
                games_played = games_played + %s WHERE user_id = %s
                """, (croutons, games_played, user_id))
        
        elif croutons and last_time_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET croutons = croutons + %s, 
                last_time_played = %s WHERE user_id = %s
                """, (croutons, last_time_played, user_id))

        elif games_played and last_time_played:
            await mycursor.execute("""
                UPDATE MacaronProfile SET games_played = games_played + %s, 
                last_time_played = %s WHERE user_id = %s
                """, (games_played, last_time_played, user_id))

        await db.commit()
        await mycursor.close()

    async def delete_macaron_profile(self, user_id: int) -> None:
        """ Deletes a Macaron Profile.
        :param user_id: The ID of the user to delete. """

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM MacaronProfile WHERE user_id = %s", (user_id,))
        await db.commit()
        await mycursor.close()