import discord
from discord.ext import commands
from discord import slash_command, Option
from external_cons import the_database
import os
from typing import List, Optional, Any, Union, Dict
from PIL import ImageDraw, ImageFont, Image
from extra import utils

guild_ids: List[int] = [int(os.getenv('SERVER_ID'))]

class RegisteredItemsTable(commands.Cog):
    """ Class for managing the RegisteredItems table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_registered_items(self, ctx) -> None:
        """ Creates the RegisteredItems table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_registered_items_exists():
            return await ctx.send(f"**Table `RegisteredItems` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE RegisteredItems (
                image_name VARCHAR(50) NOT NULL,
                item_type VARCHAR(15) NOT NULL,
                item_name VARCHAR(30) NOT NULL,
                item_price INT NOT NULL,
                message_ref BIGINT DEFAULT NULL,
                reaction_ref VARCHAR(50) DEFAULT NULL,
                PRIMARY KEY(image_name)
            ) CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `RegisteredItems` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_registered_items(self, ctx) -> None:
        """ Dropss the RegisteredItems table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_registered_items_exists():
            return await ctx.send(f"**Table `RegisteredItems` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP RegisteredItems")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `RegisteredItems` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_registered_items(self, ctx) -> None:
        """ Resets the RegisteredItems table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_registered_items_exists():
            return await ctx.send(f"**Table `RegisteredItems` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM RegisteredItems")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `RegisteredItems` table, {member.mention}!**")


    async def check_table_registered_items_exists(self) -> bool:
        """ Checks whether the RegisteredItems table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'RegisteredItems'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

class RegisteredItemsSystem(commands.Cog):
    """ Class for the RegisteredItems system. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @slash_command(name="register_item", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _register_item_slash_command(self, ctx,
        name: Option(str, name="name", description="The item name.", required=True),
        kind: Option(str, name="type", description="The item type.", choices=[
            'acessories_1', 'backgrounds', 'bb_base', 'dual_hands', 'effects', 'eyes', 
            'face_furniture', 'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands',
        ], required=True),
        price: Option(int, name="price", description="The item price.", required=True),
        image_name: Option(str, name="image_name", description="The item image name.", required=True),
        message_id: Option(str, name="message_id", description="The ID of the message from which you'll buy the item.", required=False),
        emoji: Option(str, name="emoji", description="The emoji that'll be used to buy the item.", required=False),
    ) -> None:
        """ Registers an item for people to buy it. """

        member: discord.Member = ctx.author

        if message_id:
            try:
                message_id = int(message_id)
            except ValueError:
                return await ctx.respond(f"**Please, inform a valid message ID, {member.mention}!**")
        
        if await self.get_registered_item(name, image_name):
            return await ctx.respond(f"**This item is already registered, {member.mention}!**")
        
        await self.insert_registered_item(name, kind, price, image_name, message_id, emoji)
        await ctx.respond(f"**Successfully registered the `{name}` item, {member.mention}!**")


    @slash_command(name="show_registered_items", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_registered_items_slash_command(self, ctx) -> None:
        """ Shows all the registered items. """

        member: discord.Member = ctx.author

        registerd_items = await self.get_registered_items()
        formatted_registered_items = [
            f"**{regitem[2]}**: `{regitem[3]}` curbs. (**{regitem[1]}**)" for regitem in registerd_items
        ]
        items_text = 'No items registered.' if not registerd_items else '\n'.join(formatted_registered_items)
        current_time = await utils.get_time_now()

        embed = discord.Embed(
            title="__Registered Items__",
            description=items_text,
            color=member.color,
            timestamp=current_time
        )
        embed.set_footer(text=f"Requested by: {member}", icon_url=member.display_avatar)

        await ctx.respond(embed=embed)

class UserItemsTable(commands.Cog):
    """ Class for managing the UserItems table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_user_items(self, ctx) -> None:
        """ Creates the UserItems table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_user_items_exists():
            return await ctx.send(f"**Table `UserItems` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE UserItems (
                user_id BIGINT NOT NULL,
                item_name VARCHAR(30) NOT NULL,
                enable TINYINT(1) DEFAULT 0, 
                item_type VARCHAR(15) NOT NULL,
                image_name VARCHAR(50) NOT NULL,
                PRIMARY KEY(user_id, item_name),
                CONSTRAINT fk_ui_image_name FOREIGN KEY (image_name) REFERENCES RegisteredItems (image_name) ON DELETE CASCADE ON UPDATE CASCADE
            ) CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `UserItems` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_user_items(self, ctx) -> None:
        """ Dropss the UserItems table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_user_items_exists():
            return await ctx.send(f"**Table `UserItems` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP UserItems")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `UserItems` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_user_items(self, ctx) -> None:
        """ Resets the UserItems table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_user_items_exists():
            return await ctx.send(f"**Table `UserItems` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM UserItems")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `UserItems` table, {member.mention}!**")


    async def check_table_user_items_exists(self) -> bool:
        """ Checks whether the UserItems table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'UserItems'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_registered_item(self, 
        name: str, kind: str, price: int, image_name: str, message_id: Optional[int] = None, emoji: Optional[str] = None) -> None:
        """ Inserts a Registered Item.
        :param name: The name of the item.
        :param kind: The type of the item.
        :param price: The price of the item.
        :param image_name: The item image name.
        :param message_id: The ID of the messsage from which you'll buy the item. [Optional]
        :param emoji: The emoji you'll use to buy the item. [Optional] """

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO RegisteredItems (
                item_name, item_type, item_price, image_name, message_ref, reaction_ref
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, kind, price, image_name, message_id, emoji))
        await db.commit()
        await mycursor.close()

    async def get_registered_item(self, name: Optional[str] = None, image_name: Optional[str] = None) -> List[Union[str, int]]:
        """ Gets a registered item.
        :param name: The name of the item to get. [Optional]
        :param image_name: The name of the item image to get. [Optional] """

        mycursor, _ = await the_database()

        if name and image_name:
            await mycursor.execute("SELECT * FROM RegisteredItems WHERE item_name = %s OR image_name = %s", (name, image_name))
        elif name:
            await mycursor.execute("SELECT * FROM RegisteredItems WHERE item_name = %s", (name,))
        elif image_name:
            await mycursor.execute("SELECT * FROM RegisteredItems WHERE image_name = %s", (image_name,))

        registered_item = await mycursor.fetchone()
        await mycursor.close()
        return registered_item

    async def get_registered_items(self) -> List[List[Union[str, int]]]:
        """ Gets all registered items. """

        mycursor, _ = await the_database()

        await mycursor.execute("SELECT * FROM RegisteredItems")
        registered_items = await mycursor.fetchall()
        await mycursor.close()

        return registered_items

    async def delete_registered_item(self, name: Optional[str] = None, image_name: Optional[str] = None) -> None:
        """ Deletes a registered item.
        :param name: The name of the item to delete. [Optional]
        :param image_name: The name of the item image to delete. [Optional] """

        mycursor, db = await the_database()

        if name and image_name:
            await mycursor.execute("DELETE FROM RegisteredItems WHERE item_name = %s AND image_name = %s", (name, image_name))
        elif name:
            await mycursor.execute("DELETE FROM RegisteredItems WHERE item_name = %s", (name,))
        elif image_name:
            await mycursor.execute("DELETE FROM RegisteredItems WHERE image_name = %s", (image_name,))

        await db.commit()
        await mycursor.close()

class UserItemsSystem(commands.Cog):
    """ Class for UserItems system. """

    item_categories: List[str] = [
        'acessories_1', 'backgrounds', 'bb_base', 
        'dual_hands', 'effects', 'eyes', 'face_furniture', 
        'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands',
    ]

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @slash_command(name="custom_character", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _custom_character_slash_command(self, ctx, 
        member: Option(discord.Member, name="member", description="The member to whom create the profile.", required=False)) -> None:
        """ Makes a custom character image. """

        if not member:
            member = ctx.author

        await ctx.defer()
        file_path: str = await self.create_user_custom_character(ctx, member)
        await ctx.respond(file=discord.File(file_path, filename="custom_profile.png"))
        try:
            os.remove(file_path)
        except:
            pass

    @commands.command(name="custom_character")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _custom_character_command(self, ctx, member: Union[discord.Member, discord.User] = None) -> None:
        """ Makes a custom character image.
        :param member: The member to whom create the image. [Optional][Default = You] """

        if not member:
            member = ctx.author

        file_path: str = await self.create_user_custom_character(ctx, member)
        await ctx.send(file=discord.File(file_path, filename="custom_profile.png"))
        try:
            os.remove(file_path)
        except:
            pass

    async def create_user_custom_character(self, ctx, member: Union[discord.Member, discord.User]) -> str:
        """ Creates the custom user character image.
        :param member: The member for whom to create the image. """

        # Font
        # small = ImageFont.truetype("media/fonts/built titling sb.ttf", 45)

        # Open images
        async with ctx.typing():
            background = Image.open(await self.get_user_specific_item_type(member.id, 'backgrounds'))
            bb_base = Image.open(await self.get_user_specific_item_type(member.id, 'bb_base'))
            eyes = Image.open(await self.get_user_specific_item_type(member.id, 'eyes'))
            mouths = Image.open(await self.get_user_specific_item_type(member.id, 'mouths'))
            facil_hair = Image.open(await self.get_user_specific_item_type(member.id, 'facial_hair'))
            face_furniture = Image.open(await self.get_user_specific_item_type(member.id, 'face_furniture'))
            hats = Image.open(await self.get_user_specific_item_type(member.id, 'hats'))
            left_hands = Image.open(await self.get_user_specific_item_type(member.id, 'left_hands'))
            right_hands = Image.open(await self.get_user_specific_item_type(member.id, 'right_hands'))
            dual_hands = Image.open(await self.get_user_specific_item_type(member.id, 'dual_hands'))
            accessories_1 = Image.open(await self.get_user_specific_item_type(member.id, 'acessories_1'))
            effects = Image.open(await self.get_user_specific_item_type(member.id, 'effects'))
            
            # Pastes all item images
            background.paste(bb_base, (0, 0), bb_base)
            background.paste(eyes, (0, 0), eyes)
            background.paste(mouths, (0, 0), mouths)
            background.paste(facil_hair, (0, 0), facil_hair)
            background.paste(face_furniture, (0, 0), face_furniture)
            background.paste(hats, (0, 0), hats)
            background.paste(left_hands, (0, 0), left_hands)
            background.paste(right_hands, (0, 0), right_hands)
            background.paste(dual_hands, (0, 0), dual_hands)
            background.paste(accessories_1, (0, 0), accessories_1)
            background.paste(effects, (0, 0), effects)

            # pfp = await utils.get_user_pfp(member)
            # background.paste(sloth, (0, 0), sloth)

            # Saves the image
            file_path = f'media/temporary/character_{member.id}.png'
            background.save(file_path, 'png', quality=90)
            return file_path

    async def get_user_specific_item_type(self, user_id: int, item_type: str) -> str:
        """ Gets a random item of a specific type from the user.
        :param user_id: The ID of the user from whom to get the item.
        :param item_type: The type of the item to get. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT item_name, image_name FROM UserItems WHERE user_id = %s and item_type = %s and enable", (user_id, item_type))
        spec_type_items = await mycursor.fetchone()
        await mycursor.close()
        if spec_type_items and spec_type_items[1]:
            return f'./resources/{item_type}/{spec_type_items[4]}'

        else:
            return f'./resources/{item_type}/default.png'
