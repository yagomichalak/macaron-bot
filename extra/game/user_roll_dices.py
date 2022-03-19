import discord
from discord.ext import commands
from external_cons import the_database
from typing import List

class UserRollDicesTable(commands.Cog):
    """ Class for managing the UserRollDices table. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_user_roll_dices(self, ctx) -> None:
        """ Creates the UserRollDices table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_user_roll_dices_exists():
            return await ctx.send(f"**Table `UserRollDices` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE UserRollDices (
                user_id BIGINT NOT NULL,
                dices TINYINT(4),
                PRIMARY KEY(user_id)
            )
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `UserRollDices` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_user_roll_dices(self, ctx) -> None:
        """ Dropss the UserRollDices table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_user_roll_dices_exists():
            return await ctx.send(f"**Table `UserRollDices` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP UserRollDices")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `UserRollDices` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_user_roll_dices(self, ctx) -> None:
        """ Resets the UserRollDices table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_user_roll_dices_exists():
            return await ctx.send(f"**Table `UserRollDices` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM UserRollDices")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `UserRollDices` table, {member.mention}!**")


    async def check_table_user_roll_dices_exists(self) -> bool:
        """ Checks whether the UserRollDices table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'UserRollDices'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_user_roll_dices(self, user_id: int, dices: int = 1) -> None:
        """ Inserts a UserRollDices row.
        :param user_id: The ID of the user for whom to add it.
        :param dices: The initial amount of dices to insert. [Default = 1]"""

        mycursor, db = await the_database()
        await mycursor.execute("INSERT INTO UserRollDices (user_id, dices) VALUES (%s, %s)", (user_id, dices))
        await db.commit()
        await mycursor.close()

    async def get_user_roll_dices(self, user_id: int) -> List[int]:
        """ Gets the UserRollDices info from a particular user.
        :param user_id: The ID of the user from whom to get the info. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM UserRollDices WHERE user_id = %s", (user_id,))
        user_roll_dices = await mycursor.fetchone()
        await mycursor.close()
        return user_roll_dices

    async def update_user_roll_dices(self, user_id: int, increment: int) -> None:
        """ Updates a UserRollDices for a particular user.
        :param user_id: The ID of the user to update.
        :param increment: The increment to apply to the dices counter. """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE UserRollDices SET dices = dices + %s WHERE user_id = %s", (increment, user_id))
        await db.commit()
        await mycursor.close()