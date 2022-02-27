import discord
from discord.ext import commands
from external_cons import the_database
from typing import Optional, List

class RoundStatusTable(commands.Cog):
    """ Class for managing the RoundStatus table. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_round_status(self, ctx) -> None:
        """ Creates the RoundStatus table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_round_status_exists():
            return await ctx.send(f"**Table `RoundStatus` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE RoundStatus (
                user_id BIGINT NOT NULL,
                wins INT DEFAULT 0,
                losses INT DEFAULT 0,
                PRIMARY KEY(user_id)
            )
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `RoundStatus` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_round_status(self, ctx) -> None:
        """ Dropss the RoundStatus table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_round_status_exists():
            return await ctx.send(f"**Table `RoundStatus` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP RoundStatus")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `RoundStatus` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_round_status(self, ctx) -> None:
        """ Resets the RoundStatus table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_round_status_exists():
            return await ctx.send(f"**Table `RoundStatus` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM RoundStatus")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `RoundStatus` table, {member.mention}!**")


    async def check_table_round_status_exists(self) -> bool:
        """ Checks whether the RoundStatus table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'RoundStatus'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_round_status(self, user_id: int, wins: int = 0, losses: int = 0) -> None:
        """ Inserts a RoundStatus for a user.
        :param user_id: The ID of the user for whom to add it.
        :param wins: The intial amount of wins. [Default = 0]
        :param losses: The intial amount of losses. [Default = 0] """

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO RoundStatus (
                user_id, wins, losses
            ) VALUES (%s, %s, %s)
        """, (user_id, wins, losses))
        await db.commit()
        await mycursor.close()

    async def get_round_status(self, user_id: int) -> List[int]:
        """ Gets the RoundStatus from a particular user.
        :param user_id: The ID of the user from whom to get the status. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM RoundStatus WHERE user_id = %s", (user_id,))
        round_status = await mycursor.fetchone()
        await mycursor.close()
        return round_status

    async def get_round_statuses(self) -> List[List[int]]:
        """ Gets all RoundStatuses. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM RoundStatus ORDER BY wins DESC")
        round_statuses = await mycursor.fetchall()
        await mycursor.close()
        return round_statuses

    async def update_round_status(self, user_id: int, wins: Optional[int] = None, losses: Optional[int] = None) -> None:
        """ Updates a RoundStatus for a particular user.
        :param user_id: The ID of the user to update.
        :param wins: The increment value for the wins field. [Optional]
        :param losses: The increment value for the losses field. [Optional] """

        mycursor, db = await the_database()

        if wins and losses:
            await mycursor.execute("""
                UPDATE RoundStatus SET wins = wins + %s, losses = losses + %s WHERE user_id = %s
            """, (wins, losses, user_id))
        elif wins:
            await mycursor.execute("UPDATE RoundStatus SET wins = wins + %s WHERE user_id = %s", (wins, user_id))
        elif losses:
            await mycursor.execute("UPDATE RoundStatus SET losses = losses + %s WHERE user_id = %s", (losses, user_id))

        await db.commit()
        await mycursor.close()