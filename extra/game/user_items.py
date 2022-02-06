import discord
from discord.ext import commands
from external_cons import the_database
import os
from typing import List, Optional, Any, Union, Dict
from PIL import ImageDraw, ImageFont, Image
from extra import utils

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
