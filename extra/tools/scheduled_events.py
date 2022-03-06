import discord
from discord.ext import commands, tasks

from external_cons import the_database
from extra import utils

import os
from typing import List, Union, Dict
import collections

server_id: int = int(os.getenv('SERVER_ID'))
game_text_channel_id: int = int(os.getenv('GAME_TEXT_CHANNEL_ID'))

class ScheduledEventsSystem(commands.Cog):
    """ Class for managing the ScheduledEventsSystem table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @tasks.loop(seconds=60)
    async def give_monthly_crumbs(self) -> None:
        """ Checks the time for advertising Patreon. """

        current_time = await utils.get_time_now()
        current_ts = current_time.timestamp()
        # Checks whether the Patreon advertising event exists
        if not await self.get_advertising_event(event_label='monthly_crumbs'):
            # If not, creates it
            return await self.insert_advertising_event(event_label='monthly_crumbs', current_ts=current_ts-2678400)

        # Checks whether advertising time is due
        if await self.check_advertising_time(
            current_ts=int(current_ts), event_label="monthly_crumbs", ad_time=2678400):
            print('Let us reward!')
            # Updates time and advertises.
            if not (game_text_channel := self.client.get_channel(game_text_channel_id)):
                return

            guild = game_text_channel.guild

            await self.update_advertising_time(event_label="monthly_crumbs", current_ts=current_ts)


            # Dictionary with all roles to which to give crumbs
            # roles_dict: Dict[int, int] = {
            #     749238454742679634: 100, # Boosters
            #     862731111339393034: 200, # Patreon 1
            #     939334184076443680: 250, # Patreon 2
            #     942435771116318823: 350, # Patreon 3
            #     939334189684252682: 600, # Patreon 4
            # }
            roles_dict: Dict[int, int] = {
                950097355410124891: 100,  # Boosters
                942121471092875344: 200,  # Patreon 1
                942121511706300436: 250,  # Patreon 2
                942121551166308413: 350,  # Patreon 3
                950097297964929094: 600,  # Patreon 4
            }

            # Temp lists
            text_list: List[str] = []
            roles: List[discord.Role] = []

            # Loops through all roles
            for role_id, crumbs in roles_dict.items():
                if role := discord.utils.get(guild.roles, id=role_id):
                    roles.append(role)

                text_list.append(f"**<@&{role_id}>:** `{crumbs}` crumbs;")

            # Rewards all roles
            await self.reward_monthly_crumbs(guild, roles_dict)

            # Makes embed
            embed = discord.Embed(
                title="__Monthly Crumbs__",
                description='\n'.join(text_list),
                color=discord.Color.nitro_pink(),
                timestamp=current_time
            )

            # Checks whether role pings are not null
            role_pings = None if not roles else ', '.join(map(lambda r: r.mention, roles))
            # Sends message
            await game_text_channel.send(content=role_pings, embed=embed)

    async def reward_monthly_crumbs(self, guild: discord.Guild, roles_dict: Dict[int, int]) -> None:
        """ Rewards all Booster and Patreon roles.
        :param guild: The server to get the members from.
        :param roles_dict: The dict containing the amount of crumbs to give for each role. """


        Game = self.client.get_cog('Game')

        members = collections.defaultdict(list)

        # Loops through each Patreon role and gets a list containing members that have them
        for member in guild.members:
            for role_id in roles_dict.keys():  # dict.keys
                if member.get_role(role_id):
                    members[role_id].append(member)

        for role_id, role_members in members.items():
            crumbs = roles_dict[role_id]
            users = list((crumbs, m.id) for m in role_members)

            # Give them money
            await Game.bulk_update_user_crumbs(users)
            print(f"\t-> {len(role_members)} members rewarded for: {role_id}")


class ScheduledEventsTable(commands.Cog):
    """ Class for managing the ScheduledEvents table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_scheduled_events(self, ctx: commands.Context) -> None:
        """ Creates the ScheduledEvents table. """

        member = ctx.author
        await ctx.message.delete()

        if await self.check_scheduled_events_exists():
            return await ctx.send(f"**Table `ScheduledEvents` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE ScheduledEvents (
                event_label VARCHAR(100) NOT NULL,
                event_ts BIGINT NOT NULL,
                PRIMARY KEY (event_label)
            )""")
        await db.commit()
        await mycursor.close()

        await ctx.send(f"**Table `ScheduledEvents` created, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_scheduled_events(self, ctx: commands.Context) -> None:
        """ Creates the ScheduledEvents table. """

        member = ctx.author
        await ctx.message.delete()

        if not await self.check_scheduled_events_exists():
            return await ctx.send(f"**Table `ScheduledEvents` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP TABLE ScheduledEvents")
        await db.commit()
        await mycursor.close()

        await ctx.send(f"**Table `ScheduledEvents` dropped, {member.mention}!**")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_scheduled_events(self, ctx: commands.Context) -> None:
        """ Creates the ScheduledEvents table. """

        member = ctx.author
        await ctx.message.delete()

        if not await self.check_scheduled_events_exists():
            return await ctx.send(f"**Table `ScheduledEvents` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM ScheduledEvents")
        await db.commit()
        await mycursor.close()

        await ctx.send(f"**Table `ScheduledEvents` reset, {member.mention}!**")

    async def check_scheduled_events_exists(self) -> bool:
        """ Checks whether the ScheduledEvents table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'ScheduledEvents'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def check_advertising_time(self, current_ts: int, event_label: str, ad_time: int) -> bool:
        """ Checks whether the advertising time is due.
        :param current_ts: The current timestamp.
        :param event_label: The label of the event
        :param ad_time: Advertising time cooldown. """

        mycursor, _ = await the_database()
        await mycursor.execute("""
            SELECT * from ScheduledEvents
            WHERE event_label = %s AND %s - event_ts >= %s
        """, (event_label, current_ts, ad_time))

        due_event = await mycursor.fetchone()
        await mycursor.close()
        if due_event:
            return True
        else:
            return False

    async def get_advertising_event(self, event_label: str) -> List[Union[str, int]]:
        """ Gets an advertising event.
        :param event_label: The label of the advertising event. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM ScheduledEvents WHERE event_label = %s", (event_label,))
        event = await mycursor.fetchone()
        await mycursor.close()
        return event

    async def insert_advertising_event(self, event_label: str, current_ts: int) -> None:
        """ Inserts an advertising event.
        :param event_label: The label of the advertising event.
        :param current_ts: The timestamp in which it was inserted. """

        mycursor, db = await the_database()
        await mycursor.execute("INSERT INTO ScheduledEvents (event_label, event_ts) VALUES (%s, %s)", (event_label, current_ts))
        await db.commit()
        await mycursor.close()

    async def update_advertising_time(self, event_label: str, current_ts: int) -> None:
        """ Updates the timestamp of the advertising event.
        :param event_label: The label of the advertising event.
        :param current_ts: The timestamp to update the event to. """

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE ScheduledEvents SET event_ts = %s WHERE event_label = %s", (current_ts, event_label))
        await db.commit()
        await mycursor.close()