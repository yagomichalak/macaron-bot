import discord
from discord.ext import commands, pages
from discord.utils import escape_mentions
from discord import slash_command, Option

from external_cons import the_database
from extra import utils
from extra.selects import ChangeItemCategoryMenuSelect


import os
from typing import List, Optional, Any, Union, Dict
from PIL import ImageDraw, ImageFont, Image

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
                exclusive TINYINT(1) DEFAULT 0,
                hidden TINYINT(1) DEFAULT 0,
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
        await mycursor.execute("DROP TABLE RegisteredItems")
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

    async def insert_registered_item(self, 
        name: str, kind: str, price: int, image_name: str, message_id: Optional[int] = None, emoji: Optional[str] = None, exclusive: Optional[bool] = False) -> None:
        """ Inserts a Registered Item.
        :param name: The name of the item.
        :param kind: The type of the item.
        :param price: The price of the item.
        :param image_name: The item image name.
        :param message_id: The ID of the messsage from which you'll buy the item. [Optional]
        :param emoji: The emoji you'll use to buy the item. [Optional]
        :param exclusive: Whether it's an exclusive item. [Optional][Default = False] """

        exclusive = 1 if exclusive else 0

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO RegisteredItems (
                item_name, item_type, item_price, image_name, message_ref, reaction_ref, exclusive
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, kind, price, image_name, message_id, emoji, exclusive))
        await db.commit()
        await mycursor.close()

    async def get_registered_item(self, name: Optional[str] = None, image_name: Optional[str] = None) -> List[Union[str, int]]:
        """ Gets a registered item.
        :param name: The name of the item to get. [Optional]
        :param image_name: The name of the item image to get. [Optional] """

        mycursor, _ = await the_database()

        if name and image_name:
            await mycursor.execute("SELECT * FROM RegisteredItems WHERE LOWER(item_name) = LOWER(%s) OR LOWER(image_name) = LOWER(%s)", (name, image_name))
        elif name:
            await mycursor.execute("SELECT * FROM RegisteredItems WHERE LOWER(item_name) = LOWER(%s)", (name,))
        elif image_name:
            await mycursor.execute("SELECT * FROM RegisteredItems WHERE LOWER(image_name) = LOWER(%s)", (image_name,))

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

    async def get_registered_items_ordered_by_price(self) -> List[List[Union[str, int]]]:
        """ Gets all registered items ordered by price. """

        mycursor, _ = await the_database()

        await mycursor.execute("SELECT * FROM RegisteredItems ORDER BY item_price DESC")
        registered_items = await mycursor.fetchall()
        await mycursor.close()

        return registered_items

    async def update_item_exclusive(self, item_name: str, maybe: Optional[bool] = True) -> None:
        """ Changes the item's exclusive state.
        :param item_name: The name of the item to update.
        :param maybe: Whether to make or unmake it exclusive. [Optional][Default = True] """

        maybe = 1 if maybe else 0

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE RegisteredItems SET exclusive = %s WHERE LOWER(item_name) = LOWER(%s)", (maybe, item_name))
        await db.commit()
        await mycursor.close()

    async def update_item_hidden(self, item_name: str, maybe: Optional[bool] = True) -> None:
        """ Changes the item's hidden state.
        :param item_name: The name of the item to update.
        :param maybe: Whether to make or unmake it hidden. [Optional][Default = True] """

        maybe = 1 if maybe else 0

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE RegisteredItems SET hidden = %s WHERE LOWER(item_name) = LOWER(%s)", (maybe, item_name))
        await db.commit()
        await mycursor.close()

    async def delete_registered_item(self, name: Optional[str] = None, image_name: Optional[str] = None) -> None:
        """ Deletes a registered item.
        :param name: The name of the item to delete. [Optional]
        :param image_name: The name of the item image to delete. [Optional] """

        mycursor, db = await the_database()

        if name and image_name:
            await mycursor.execute("DELETE FROM RegisteredItems WHERE LOWER(item_name) = LOWER(%s) AND LOWER(image_name) = LOWER(%s)", (name, image_name))
        elif name:
            await mycursor.execute("DELETE FROM RegisteredItems WHERE LOWER(item_name) = LOWER(%s)", (name,))
        elif image_name:
            await mycursor.execute("DELETE FROM RegisteredItems WHERE LOWER(image_name) = LOWER(%s)", (image_name,))

        await db.commit()
        await mycursor.close()

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
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 'dual_hands', 'effects', 'eyes', 
            'face_furniture', 'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands', 'outfits'
        ], required=True),
        price: Option(int, name="price", description="The item price.", required=True),
        image_name: Option(str, name="image_name", description="The item image name.", required=True),
        exclusive: Option(bool, name="exclusive", description="Whether the item is exclusive.", required=False, default=False),
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
        
        await self.insert_registered_item(name, kind, price, image_name, message_id, emoji, exclusive)
        await ctx.respond(f"**Successfully registered the `{name}` item, {member.mention}!**")


    @slash_command(name="shop", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_registered_items_slash_command(self, ctx,
        item_category: Option(str, name="item_category", description="The item category to show.", choices=[
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 'dual_hands', 'effects', 'eyes', 
            'face_furniture', 'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands', 'outfits'
        ], required=False, default='All')) -> None:
        """ Shows all registered items. """

        await ctx.defer()
        registered_items = await self.get_registered_items_ordered_by_price()

        self.pages = registered_items
        view = discord.ui.View()
        select = ChangeItemCategoryMenuSelect(registered_items)
        formatted_items = await select.sort_registered_items(item_category)
        # view.add_item(select)

        paginator = pages.Paginator(pages=formatted_items, custom_view=view)
        await paginator.respond(ctx.interaction, ephemeral=False)

    @commands.command(name="shop", aliases=["show_registered_items", "registered_items"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_registered_items_command(self, ctx, item_category: Optional[str] = 'All') -> None:
        """ Shows all registered items.
        :param item_category: The item category to show. [Optional][Default = All] """

        member: discord.Member = ctx.author
        if item_category.lower() != 'all':
            if item_category.lower() not in self.item_categories:
                return await ctx.send(
                    f"**Please, inform a valid item category, {member.mention}!**\n`{', '.join(self.item_categories)}`")


        registered_items = await self.get_registered_items_ordered_by_price()

        self.pages = registered_items
        view = discord.ui.View()
        select = ChangeItemCategoryMenuSelect(registered_items)
        formatted_items = await select.sort_registered_items(item_category)
        # view.add_item(select)

        paginator = pages.Paginator(pages=formatted_items, custom_view=view)
        await paginator.send(ctx)

    @slash_command(name="hidden_items", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _show_hidden_registered_items_slash_command(self, ctx,
        item_category: Option(str, name="item_category", description="The item category to show.", choices=[
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 'dual_hands', 'effects', 'eyes', 
            'face_furniture', 'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands', 'outfits'
        ], required=False, default='All')) -> None:
        """ Shows all hidden registered items. """

        await ctx.defer(ephemeral=True)
        registered_items = await self.get_registered_items_ordered_by_price()

        self.pages = registered_items
        view = discord.ui.View()
        select = ChangeItemCategoryMenuSelect(registered_items)
        formatted_items = await select.sort_registered_items(item_category, hidden=True)
        # view.add_item(select)

        paginator = pages.Paginator(pages=formatted_items, custom_view=view)
        await paginator.respond(ctx.interaction, ephemeral=True)

    @slash_command(name="black_market", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_exclusive_registered_items_slash_command(self, ctx,
        item_category: Option(str, name="item_category", description="The item category to show.", choices=[
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 'dual_hands', 'effects', 'eyes', 
            'face_furniture', 'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands', 'outfits'
        ], required=False, default='All')) -> None:
        """ Shows all exclusive registered items. """

        await ctx.defer()
        registered_items = await self.get_registered_items_ordered_by_price()

        self.pages = registered_items
        view = discord.ui.View()
        select = ChangeItemCategoryMenuSelect(registered_items)
        formatted_items = await select.sort_registered_items(item_category, exclusive=True)
        # view.add_item(select)

        paginator = pages.Paginator(pages=formatted_items, custom_view=view)
        await paginator.respond(ctx.interaction, ephemeral=False)

    @commands.command(name="black_market", aliases=[
        "show_exclusive_items", "exclusive_items", "exclusiveitems",
        "blackmarket", "blackshop", "show_exclusive" "showexclusive"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_exclusive_registered_items_command(self, ctx, item_category: Optional[str] = 'All') -> None:
        """ Shows all exclusive registered items.
        :param item_category: The item category to show. [Optional][Default = All] """

        member: discord.Member = ctx.author
        if item_category.lower() != 'all':
            if item_category.lower() not in self.item_categories:
                return await ctx.send(
                    f"**Please, inform a valid item category, {member.mention}!**\n`{', '.join(self.item_categories)}`")


        registered_items = await self.get_registered_items_ordered_by_price()

        self.pages = registered_items
        view = discord.ui.View()
        select = ChangeItemCategoryMenuSelect(registered_items)
        formatted_items = await select.sort_registered_items(item_category, exclusive=True)
        # view.add_item(select)

        paginator = pages.Paginator(pages=formatted_items, custom_view=view)
        await paginator.send(ctx)


    @slash_command(name="unregister_item", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def _unregister_item_slash_command(self, ctx,
        name: Option(str, name="name", description="The item name.", required=True)
    ) -> None:
        """ Registers an item for people to buy it. """

        member: discord.Member = ctx.author

        
        if not await self.get_registered_item(name=name):
            return await ctx.respond(f"**This item is not even registered, {member.mention}!**")
        
        await self.delete_registered_item(name)
        await ctx.respond(f"**Successfully deleted the registered item `{name}`, {member.mention}!**")

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
        await mycursor.execute("DROP TABLE UserItems")
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

    async def insert_user_item(self, user_id: int, item_name: str, item_type: str, image_name: str) -> None:
        """ Inserts an item to the user inventory.
        :param user_id: The ID of the user owner of the item.
        :param item_name: The item name.
        :param item_type: The item type.
        :param image_name: The item image name. """

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO UserItems (
                user_id, item_name, item_type, image_name
            ) VALUES (%s, %s, %s, %s)
        """, (user_id, item_name, item_type, image_name))
        await db.commit()
        await mycursor.close()

    async def get_user_item(self, user_id: int, item_name: str) -> List[Union[int, str]]:
        """ Gets an item from the user inventory.
        :param user_id: The ID of the user owner of the item.
        :param item_name: The name of the item to get. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM UserItems WHERE user_id = %s AND LOWER(item_name) = LOWER(%s)", (user_id, item_name))
        user_item = await mycursor.fetchone()
        await mycursor.close()
        return user_item

    async def get_user_items(self, user_id: int) -> List[List[Union[int, str]]]:
        """ Gets an item from the user inventory.
        :param user_id: The ID of the user owner of the item. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM UserItems WHERE user_id = %s", (user_id,))
        user_items = await mycursor.fetchall()
        await mycursor.close()
        return user_items

    async def update_item_equipped(self, user_id: int, item_name: str, enable: Optional[bool] = False) -> None:
        """ Updates the user item's equipped state.
        :param user_id: The ID of the user.
        :param item_name: The item to update.
        :param enable: Whether it's to equip or unequip. [Optional][Default = False] """

        enable = 1 if enable else 0

        mycursor, db = await the_database()
        await mycursor.execute("UPDATE UserItems SET enable = %s WHERE user_id = %s AND LOWER(item_name) = LOWER(%s)", (enable, user_id, item_name))
        await db.commit()
        await mycursor.close()

    async def delete_user_item(self, user_id: int, item_name: str) -> None:
        """ Deletes an item from the user's inventory.
        :param user_id: The ID of the user from whom to remove the item.
        :param item_name: The name of the item to remove. """

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM UserItems WHERE user_id = %s AND LOWER(item_name) = LOWER(%s)", (user_id, item_name))
        await db.commit()
        await mycursor.close()

class UserItemsSystem(commands.Cog):
    """ Class for UserItems system. """

    item_categories: List[str] = [
        'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 
        'dual_hands', 'effects', 'eyes', 'face_furniture', 
        'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands',
        'outfits'
    ]

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @slash_command(name="character", guild_ids=guild_ids)
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

    @commands.command(name="character", aliases=["custom_character"])
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
            background = Image.open(await self.get_user_specific_item_type(member.id, 'backgrounds')).convert('RGBA')
            bb_base = Image.open(await self.get_user_specific_item_type(member.id, 'bb_base')).convert('RGBA')
            eyes = Image.open(await self.get_user_specific_item_type(member.id, 'eyes')).convert('RGBA')
            effects = Image.open(await self.get_user_specific_item_type(member.id, 'effects')).convert('RGBA')
            mouths = Image.open(await self.get_user_specific_item_type(member.id, 'mouths')).convert('RGBA')
            facial_hair = Image.open(await self.get_user_specific_item_type(member.id, 'facial_hair')).convert('RGBA')
            face_furniture = Image.open(await self.get_user_specific_item_type(member.id, 'face_furniture')).convert('RGBA')
            hats = Image.open(await self.get_user_specific_item_type(member.id, 'hats')).convert('RGBA')
            left_hands = Image.open(await self.get_user_specific_item_type(member.id, 'left_hands')).convert('RGBA')
            right_hands = Image.open(await self.get_user_specific_item_type(member.id, 'right_hands')).convert('RGBA')
            accessories_1 = Image.open(await self.get_user_specific_item_type(member.id, 'accessories_1')).convert('RGBA')
            accessories_2 = Image.open(await self.get_user_specific_item_type(member.id, 'accessories_2')).convert('RGBA')
            outfits = Image.open(await self.get_user_specific_item_type(member.id, 'outfits')).convert('RGBA')
            dual_hands = Image.open(await self.get_user_specific_item_type(member.id, 'dual_hands')).convert('RGBA')
            
            # Gets the user's hidden item categories.
            all_hidden_icats = await self.get_hidden_item_categories(member.id)
            hidden_icats = list(map(lambda ic: ic[1], all_hidden_icats))

            # Pastes all item images
            if not 'accessories_1' in hidden_icats: background.paste(accessories_1, (0, 0), accessories_1)
            if not 'bb_base' in hidden_icats: background.paste(bb_base, (0, 0), bb_base)
            if not 'eyes' in hidden_icats: background.paste(eyes, (0, 0), eyes)
            if not 'facial_hair' in hidden_icats: background.paste(facial_hair, (0, 0), facial_hair)
            if not 'effects' in hidden_icats: background.paste(effects, (0, 0), effects)
            if not 'mouths' in hidden_icats: background.paste(mouths, (0, 0), mouths)
            if not 'face_furniture' in hidden_icats: background.paste(face_furniture, (0, 0), face_furniture)
            if not 'hats' in hidden_icats: background.paste(hats, (0, 0), hats)
            if not 'left_hands' in hidden_icats: background.paste(left_hands, (0, 0), left_hands)
            if not 'right_hands' in hidden_icats: background.paste(right_hands, (0, 0), right_hands)
            if not 'accessories_2' in hidden_icats: background.paste(accessories_2, (0, 0), accessories_2)
            if not 'outfits' in hidden_icats: background.paste(outfits, (0, 0), outfits)
            if not 'dual_hands' in hidden_icats: background.paste(dual_hands, (0, 0), dual_hands)

            # pfp = await utils.get_user_pfp(member)
            # background.paste(pfp, (0, 0), pfp)

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
            return f'./resources/{item_type}/{spec_type_items[1]}'

        else:
            return f'./resources/{item_type}/default.png'

    @commands.command(aliases=["inventory", "items", "inv"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def user_inventory(self, ctx, member: Optional[discord.Member] = None) -> None:
        """ Checks the user's inventory.
        :param member: The member from whom to show the inventory. [Optional][Default = You] """

        if not member:
            member = ctx.author

        user_items = await self.get_user_items(member.id)

        formatted_user_items = [
            f"**{uitem[1]}**: `{uitem[3]}`  (**{'Equipped' if uitem[2] else 'Unequipped'}**)" for uitem in user_items
        ]
        items_text = 'No items.' if not user_items else '\n'.join(formatted_user_items)
        current_time = await utils.get_time_now()

        embed = discord.Embed(
            title="__User Inventory__",
            description=items_text,
            color=member.color,
            timestamp=current_time
        )
        embed.set_footer(text=f"Requested by: {member}", icon_url=member.display_avatar)

        await ctx.send(embed=embed)

    @commands.command(aliases=['equip'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def equip_item(self, ctx, *, item_name: str = None) -> None:
        """ Equips an item.
        :param item_name: The name of the item to equip. """

        member: discord.Member = ctx.author
        if not item_name:
            return await ctx.send(f"**Please, inform an item to equip, {member.mention}!**")

        if not (user_item := await self.get_user_item(member.id, item_name)):
            return await ctx.send(f"**You don't have this item to equip, {member.mention}!**")

        if user_item[2]:
            return await ctx.send(f"**This item is already equipped, {member.mention}!**")

        if await self.check_user_can_change_item_state(member.id, item_name, True):
            return await ctx.send(f"**You already have a __{user_item[3]}__ item equipped!**")

        await self.update_item_equipped(member.id, item_name, True)
        await ctx.send(f"**{member.mention} equipped __{item_name.title()}__!**")

    @commands.command(aliases=["unequip"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def unequip_item(self, ctx, *, item_name: str = None) -> None:
        """ Unequips an item.
        :param item_name: The item to unequip """

        member: discord.Member = ctx.author

        if not item_name:
            return await ctx.send("**Inform an item to unequip!**")

        if not (user_item := await self.get_user_item(member.id, item_name)):
            return await ctx.send(f"**You don't have this item, {member.mention}!**")

        if not user_item[2]:
            return await ctx.send(f"**This item is already unequipped, {member.mention}!**")

        await self.update_item_equipped(member.id, item_name)
        await ctx.send(f"**{member.mention} unequipped __{item_name.title()}__!**")

    async def check_user_can_change_item_state(self, user_id: int, item_name: str, enable: bool = False) -> bool:
        """ Checks whether a user can equip or unequip a specific item.
        :param user_id: The ID of the user to check.
        :param item_name: The name of the item.
        :param enable: Whether to check if you can equip or unequip. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT item_type FROM UserItems WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        item_type = await mycursor.fetchone()

        enable = 1 if enable else 0
        await mycursor.execute(
            "SELECT * FROM UserItems WHERE user_id = %s AND LOWER(item_type) = LOWER(%s) AND enable = %s", (user_id, item_type, enable))
        equipped_item = await mycursor.fetchone()
        await mycursor.close()

        if equipped_item and item_type:
            return True

        return False


    @commands.command(aliases=["buy"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def buy_item(self, ctx, *, item_name: str = None) -> None:
        """ (ADM) Buys an item from the shop.
        :param item_name: The name of the item. """

        member: discord.Member = ctx.author

        if not item_name:
            return await ctx.send("**Inform an item to buy!**")

        item_name = escape_mentions(item_name)

        if await self.get_user_item(member.id, item_name):
            return await ctx.send(f"**You already have that item!**")

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {member.mention}!**")

        if not (user_profile := await self.get_macaron_profile(member.id)):
            await ctx.send(f"**You don't have any money to buy this item, {member.mention}!**")
            return await self.insert_macaron_profile(member.id)

        if user_profile[1] < regitem[3]:
            return await ctx.send(f"**The item costs `{regitem[3]}`{self.crumbs_emoji}, you have `{user_profile[1]}`{self.crumbs_emoji}, {member.mention}!**")

        if regitem[7]:
            return await ctx.send(f"**You cannot buy a hidden item, {member.mention}!**")

        if regitem[6]:
            exclusive_roles = await self.get_exclusive_item_roles(regitem[2])
            if not exclusive_roles:
                return await ctx.send(f"**You cannot buy this exclusive item, {member.mention}!**")

            if not set([mr.id for mr in member.roles]) & set(list(map(lambda er: er[0], exclusive_roles))):
                return await ctx.send(f"**You don't have any of the required roles to buy this item, {member.mention}!**")

        await self.update_user_money(member.id, -regitem[3])
        await self.insert_user_item(member.id, regitem[2], regitem[1], regitem[0])
        return await ctx.send(f"**You just bought `{regitem[2].title()}`, {member.name}!**")

    @commands.command(aliases=["make_hidden"])
    @commands.has_permissions(administrator=True)
    async def make_item_hidden(self, ctx, *, item_name: str = None) -> None:
        """ (ADM) Makes an item hidden.
        :param item_name: The name of the item. """

        member: discord.Member = ctx.author

        if not item_name:
            return await ctx.send("**Inform an item to update!**")

        item_name = escape_mentions(item_name)

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {member.mention}!**")

        if regitem[7]:
            return await ctx.send(f"**This item is already hidden, {member.mention}!**")

        await self.update_item_hidden(regitem[2])
        return await ctx.send(f"**The `{regitem[2].title()}` item is now hidden, {member.name}!**")

    @commands.command(aliases=["unmake_hidden"])
    @commands.has_permissions(administrator=True)
    async def unmake_item_hidden(self, ctx, *, item_name: str = None) -> None:
        """ (ADM) Makes an item not hidden.
        :param item_name: The name of the item. """

        member: discord.Member = ctx.author

        if not item_name:
            return await ctx.send("**Inform an item to update!**")

        item_name = escape_mentions(item_name)

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {member.mention}!**")

        if not regitem[7]:
            return await ctx.send(f"**This item is not even hidden, {member.mention}!**")

        await self.update_item_hidden(regitem[2], False)
        return await ctx.send(f"**The `{regitem[2].title()}` item is no longer hidden, {member.name}!**")

    @commands.command(aliases=["make_exclusive"])
    @commands.has_permissions(administrator=True)
    async def make_item_exclusive(self, ctx, *, item_name: str = None) -> None:
        """ (ADM) Makes an item exclusive.
        :param item_name: The name of the item. """

        member: discord.Member = ctx.author

        if not item_name:
            return await ctx.send("**Inform an item to update!**")

        item_name = escape_mentions(item_name)

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {member.mention}!**")

        if regitem[6]:
            return await ctx.send(f"**This item is already exclusive, {member.mention}!**")

        await self.update_item_exclusive(regitem[2])
        return await ctx.send(f"**The `{regitem[2].title()}` item is now exclusive, {member.name}!**")

    @commands.command(aliases=["unmake_exclusive"])
    @commands.has_permissions(administrator=True)
    async def unmake_item_exclusive(self, ctx, *, item_name: str = None) -> None:
        """ (ADM) Makes an item not exclusive.
        :param item_name: The name of the item. """

        member: discord.Member = ctx.author

        if not item_name:
            return await ctx.send("**Inform an item to update!**")

        item_name = escape_mentions(item_name)

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {member.mention}!**")

        if not regitem[6]:
            return await ctx.send(f"**This item is not even exclusive, {member.mention}!**")

        await self.update_item_exclusive(regitem[2], False)
        await self.delete_exclusive_item_roles(regitem[2])
        return await ctx.send(f"**The `{regitem[2].title()}` item is no longer exclusive, {member.name}!**")

    @commands.command(aliases=["give_member_item", "add_item", "give_item"])
    @commands.has_permissions(administrator=True)
    async def add_member_item(self, ctx, member: discord.Member = None, *, item_name: str = None) -> None:
        """ (ADM) Gives an item to a member.
        :param member: The member to give the item.
        :param item_name: The name of the item. """

        if not member:
            return await ctx.send("**Inform a member!**")

        if not item_name:
            return await ctx.send("**Inform an item to add!**")

        item_name = escape_mentions(item_name)

        if await self.get_user_item(member.id, item_name):
            return await ctx.send(f"**{member.name} already has that item!**")

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {ctx.author.mention}!**")

        await self.insert_user_item(member.id, regitem[2], regitem[1], regitem[0])
        return await ctx.send(f"**Successfully given `{regitem[2].title()}` to {member.name}!**")

    @commands.command(aliases=["delete_member_item", "remove_item", "delete_item"])
    @commands.has_permissions(administrator=True)
    async def remove_member_item(self, ctx, member: discord.Member = None, *, item_name: str = None) -> None:
        """ (ADM) Gives an item to a member.
        :param member: The member to give the item.
        :param item_name: The name of the item. """

        if not member:
            return await ctx.send("**Inform a member!**")

        if not item_name:
            return await ctx.send("**Inform an item to add!**")

        item_name = escape_mentions(item_name)

        if not await self.get_user_item(member.id, item_name):
            return await ctx.send(f"**{member.name} doesn't even have that item!**")

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {ctx.author.mention}!**")

        await self.delete_user_item(member.id, regitem[2])
        return await ctx.send(f"**Successfully removed `{regitem[2].title()}` from {member.name}!**")

    @commands.command(aliases=['addcrumbs', 'give_crumbs', 'givecrumbs'])
    @commands.has_permissions(administrator=True)
    async def add_crumbs(self, ctx, member: discord.Member = None, amount: int = None):
        """ Adds crumbs to a user.
        :param member: The member to whom give the crumbs.
        :param amount: The amount of crumbs to add. (Can be negative.) """

        author: discord.Member = ctx.author
        if not member:
            return await ctx.send(f"**Please, inform a user to whom give the crumbs, {author.mention}!**")

        if amount is None:
            return await ctx.send(f"**Please, inform an amount of crumbs to give, {author.mention}!**")
    
        await self.update_user_money(member.id, amount)
        await ctx.send(f"**Added `{amount}` {self.crumbs_emoji} to {member.mention}!**")

    @slash_command(name="hide", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _hide_slash_command(self, ctx, 
        item_category: Option(str, name="item_category", description="The category to hide.", choices=[
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 
            'dual_hands', 'effects', 'eyes', 'face_furniture', 
            'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands',
            'outfits'
        ], required=True)) -> None:
        """ Hides an item category so it won't show on your custom profile. """

        member: discord.Member = ctx.author
        await ctx.defer()
        await self._hide_unhide_command_callback(ctx, member, item_category)

    @slash_command(name="unhide", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _unhide_slash_command(self, ctx,
        item_category: Option(str, name="item_category", description="The category to unhide.", choices=[
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 
            'dual_hands', 'effects', 'eyes', 'face_furniture', 
            'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands',
            'outfits'
        ], required=True)) -> None:
        """ Unhides an item category so it will show on your custom profile again.
        :param item_category: The category to unhide. """

        member: discord.Member = ctx.author
        await ctx.defer()
        await self._hide_unhide_command_callback(ctx, member, item_category, False)

    @commands.command(name="hide", aliases=["omit", "cacher"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _hide_command(self, ctx, item_category: str = None) -> None:
        """ Hides an item category so it won't show on your custom profile.
        :param item_category: The category to hide. """

        member: discord.Member = ctx.author
        await self._hide_unhide_command_callback(ctx, member, item_category)

    @commands.command(name="unhide", aliases=["include"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _unhide_command(self, ctx, item_category: str = None) -> None:
        """ Unhides an item category so it will show on your custom profile again.
        :param item_category: The category to unhide. """

        member: discord.Member = ctx.author
        await self._hide_unhide_command_callback(ctx, member, item_category, False)

    async def _hide_unhide_command_callback(self, ctx, member: discord.Member, item_category: str, hide: Optional[bool] = True) -> None:
        """ Hides or unhides an item category for a user.
        :param ctx: The context of the command.
        :param member: The member for whom to hide/unhide the item category.
        :param item_category: The item category to hide/unhide.
        :param hide: Whether it's to hide the comamnd. [Optional][Default = True] """

        answer: discord.PartialMessageable = ctx.send if isinstance(ctx, commands.Context) else ctx.respond
        hide_kw: str = 'hide' if hide else 'unhide'
        categories_text: str  = ', '.join(self.item_categories)

        if not item_category:
            return await answer(f"**Please, inform an item category to {hide_kw}, {member.mention}!\n`{categories_text}`**")

        if item_category.lower() not in self.item_categories:
            return await answer(f"**Please, inform a valid item category, {member.mention}!\n`{categories_text}`**")

        if hide: # Hide            
            if await self.get_hidden_item_category(member.id, item_category):
                return await answer(f"**The `{item_category}` item category is already hidden for you, {member.mention}!**")

            await self.insert_hidden_item_category(member.id, item_category)
            await answer(f"**Successfully hid the `{item_category}` item category, {member.mention}!**")

        else: # Unhide
            if not await self.get_hidden_item_category(member.id, item_category):
                return await answer(f"**The `{item_category}` item category is not even hidden for you, {member.mention}!**")

            await self.delete_hidden_item_category(member.id, item_category)
            await answer(f"**Successfully unhid the `{item_category}` item category, {member.mention}!**")

    @slash_command(name="show_hidden_categories", guild_ids=guild_ids)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_hidden_categories_slash_command(self, ctx,
        member: Option(discord.Member, name="member", description="The member for whom to show them.", required=False)) -> None:
        """ Shows your hidden item categories. """

        if not member:
            member: discord.Member = ctx.author

        await ctx.defer()
        await self._show_hidden_categories_command_callback(ctx, member)

    @commands.command(name="show_hidden_categories", aliases=["show_hidden", "show_hidden_items", "hidden_categories"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _show_hidden_categories_command(self, ctx, member: discord.Member = None) -> None:
        """ Shows your hidden item categories.
        :param member: The member for whom to show them."""

        if not member:
            member: discord.Member = ctx.author

        await self._show_hidden_categories_command_callback(ctx, member)

    async def _show_hidden_categories_command_callback(self, ctx, member: discord.Member) -> None:
        """ Callback for the show hidden item categories command. """

        answer: discord.PartialMessageable = ctx.send if isinstance(ctx, commands.Context) else ctx.respond
        author: discord.Member = ctx.author

        if not (user_items := await self.get_hidden_item_categories(member.id)):
            if ctx.author.id == member.id:
                return await answer(f"**You don't have any hidden item categories, {member.mention}!**")
            else:
                return await answer(f"**This user doesn't have any hidden item categories, {author.mention}!**")
        
        formatted_item_categories: str = ', '.join(list(map(lambda ic: ic[1], user_items)))

        current_time = await utils.get_time_now()
        embed = discord.Embed(
            title="__Hidden Item Categories__",
            description=formatted_item_categories,
            color=member.color,
            timestamp=current_time
        )
        embed.set_thumbnail(url=member.display_avatar)
        embed.set_author(name=member, icon_url=member.display_avatar)
        embed.set_footer(text=f"Requested by: {author}", icon_url=author.display_avatar)
        await answer(embed=embed)

    @slash_command(name="add_exclusive_item_role", guild_ids=guild_ids)
    @commands.has_permissions(administrator=True)
    async def _add_exclusive_item_role_slash_command(self, ctx, 
        role: Option(discord.Role, name="role", description="The role to add access to the item."),
        item_name: Option(str, name="item_name", description="The name of the item.")
        ) -> None:
        """ (ADM) Adds an exclusive item role. """

        await ctx.defer()
        await self._add_exclusive_item_role_callback(ctx, role, item_name)

    @commands.command(name="add_exclusive_item_role", aliases=["add_exclusive_role", "addexclusive", "add_exclusive"])
    @commands.has_permissions(administrator=True)
    async def _add_exclusive_item_role_command(self, ctx, role: discord.Role = None, *, item_name: str = None) -> None:
        """ (ADM) Adds an exclusive item role.
        :param role: The role to add access to the item.
        :param item_name: The name of the item. """

        await self._add_exclusive_item_role_callback(ctx, role, item_name)

    async def _add_exclusive_item_role_callback(self, ctx, role: discord.Role, item_name: str) -> None:
        """ Callback for the command that adds an exclusive item role.
        :param ctx: The context of the command.
        :param role: The role to give access to the item.
        :param item_name: The name of the item to attach to the role. """

        answer: discord.PartialMessageable = ctx.send if isinstance(ctx, commands.Context) else ctx.respond
        member: discord.Member = ctx.author

        if not role:
            return await answer(f"**Please, inform a role to give access to the item, {member.mention}!**")

        if not item_name:
            return await answer(f"**Inform an item to attach to the role, {member.mention}!**")

        item_name = escape_mentions(item_name)

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await answer(f"**This item doesn't exist, {member.mention}!**")

        if await self.get_exclusive_item_role(item_name, role.id):
            return await answer(f"**This item is already exclusive to this role, {member.mention}!**")

        await self.insert_exclusive_item_role(role.id, regitem[2], regitem[0])
        await self.update_item_exclusive(regitem[2])
        return await answer(f"**The `{regitem[2]}` item is now exclusive to the `{role}` role, {member.name}!**")

    @slash_command(name="delete_exclusive_item_role", guild_ids=guild_ids)
    @commands.has_permissions(administrator=True)
    async def _delete_exclusive_item_role_slash_command(self, ctx, 
        role: Option(discord.Role, name="role", description="The role to remove access from the item."),
        item_name: Option(str, name="item_name", description="The name of the item.")
        ) -> None:
        """ (ADM) Removes an exclusive item role. """

        await ctx.defer()
        await self._delete_exclusive_item_role_callback(ctx, item_name, role)

    @commands.command(name="delete_exclusive_item_role", aliases=[
        "delete_exclusive_role", "delexclusive", "delete_exclusive",
        "remove_exclusive", "removeexclusive"
    ])
    @commands.has_permissions(administrator=True)
    async def _delete_exclusive_item_role_command(self, ctx, role: discord.Role = None, *, item_name: str = None) -> None:
        """ (ADM) Removes an exclusive item role.
        :param role: The role to remove access from the item.
        :param item_name: The name of the item. """

        await self._delete_exclusive_item_role_callback(ctx, item_name, role)

    @slash_command(name="delete_exclusive_item_roles", guild_ids=guild_ids)
    @commands.has_permissions(administrator=True)
    async def _delete_exclusive_item_roles_slash_command(self, ctx, 
        item_name: Option(str, name="item_name", description="The name of the item.") ) -> None:
        """ (ADM) Removes all exclusive item roles from an item. """

        await ctx.defer()
        await self._delete_exclusive_item_role_callback(ctx, item_name, all=True)

    @commands.command(name="delete_exclusive_item_roles", aliases=[
        "delete_exclusive_roles", "delexclusives", "delete_exclusives",
        "remove_exclusives", "removeexclusives"
    ])
    @commands.has_permissions(administrator=True)
    async def _delete_exclusive_item_roles_command(self, ctx, *, item_name: str = None) -> None:
        """ (ADM) Removes all exclusive item roles.
        :param item_name: The name of the item. """

        await self._delete_exclusive_item_role_callback(ctx, item_name, all=True)

    async def _delete_exclusive_item_role_callback(self, ctx, item_name: str, role: discord.Role = None, all: bool = False) -> None:
        """ Callback for the command that removes an exclusive item role.
        :param ctx: The context of the command.
        :param item_name: The name of the item to dettach from the role.
        :param role: The role to take access from the item. [Optional]
        :param all: Whether to delete all roles. [Optional][Default = False] """

        answer: discord.PartialMessageable = ctx.send if isinstance(ctx, commands.Context) else ctx.respond
        member: discord.Member = ctx.author

        if not role and not all:
            return await answer(f"**Please, inform a role to remove access from the item, {member.mention}!**")

        if not item_name:
            return await answer(f"**Inform an item to dettach from the role, {member.mention}!**")

        item_name = escape_mentions(item_name)

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await answer(f"**This item doesn't exist, {member.mention}!**")

        if all:
            if not await self.get_exclusive_item_roles(item_name):
                return await answer(f"**This item is not even exclusive to any role, {member.mention}!**")

            await self.delete_exclusive_item_roles(item_name)
            return await answer(f"**The `{regitem[2]}` item is no longer exclusive to any role, {member.name}!**")
        else:
            if not await self.get_exclusive_item_role(item_name, role.id):
                return await answer(f"**This item is not even exclusive to this role, {member.mention}!**")

            await self.delete_exclusive_item_role(item_name, role.id)
            return await answer(f"**The `{regitem[2]}` item is no longer exclusive to the `{role}` role, {member.name}!**")

class HiddenItemCategoryTable(commands.Cog):
    """ Class for managing the HiddenItemCategory table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_hidden_item_category(self, ctx) -> None:
        """ Creates the HiddenItemCategory table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_hidden_item_category_exists():
            return await ctx.send(f"**Table `HiddenItemCategory` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE HiddenItemCategory (
                user_id BIGINT NOT NULL,
                item_type VARCHAR(15) NOT NULL,
                PRIMARY KEY(user_id, item_type)
            )
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `HiddenItemCategory` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_hidden_item_category(self, ctx) -> None:
        """ Dropss the HiddenItemCategory table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_hidden_item_category_exists():
            return await ctx.send(f"**Table `HiddenItemCategory` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP TABLE HiddenItemCategory")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `HiddenItemCategory` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_hidden_item_category(self, ctx) -> None:
        """ Resets the HiddenItemCategory table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_hidden_item_category_exists():
            return await ctx.send(f"**Table `HiddenItemCategory` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM HiddenItemCategory")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `HiddenItemCategory` table, {member.mention}!**")


    async def check_table_hidden_item_category_exists(self) -> bool:
        """ Checks whether the HiddenItemCategory table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'HiddenItemCategory'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_hidden_item_category(self, user_id: int, item_category: str) -> None:
        """ Inserts a Hidden Item Category for the user.
        :param user_id: The ID of the user.
        :param item_category: The item category to hide. """

        mycursor, db = await the_database()
        await mycursor.execute("INSERT INTO HiddenItemCategory (user_id, item_type) VALUES (%s, %s)", (user_id, item_category.lower()))
        await db.commit()
        await mycursor.close()

    async def get_hidden_item_category(self, user_id: int, item_category: str) -> List[Union[int, str]]:
        """ Gets a specific Hidden Item Category.
        :param user_id: The ID of the user from whom to get it.
        :param item_category: The item category to get. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM HiddenItemCategory WHERE user_id = %s AND item_type = %s", (user_id, item_category.lower()))
        hidden_item_category = await mycursor.fetchone()
        await mycursor.close()
        return hidden_item_category

    async def get_hidden_item_categories(self, user_id: int) -> List[List[Union[int, str]]]:
        """ Gets all Hidden Item Categories from the user.
        :param user_id: The ID of the user from whom to get them. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM HiddenItemCategory WHERE user_id = %s", (user_id,))
        hidden_item_categories = await mycursor.fetchall()
        await mycursor.close()
        return hidden_item_categories

    async def delete_hidden_item_category(self, user_id: int, item_category: str) -> None:
        """ Deletes a Hidden Item Category.
        :param user_id: The ID of the user from whom to delete it.
        :param item_category: The category to delete. """

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM HiddenItemCategory WHERE user_id = %s AND item_type = %s", (user_id, item_category))
        await db.commit()
        await mycursor.close()

class ExclusiveItemRoleTable(commands.Cog):
    """ Class for managing the ExclusiveItemRole table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def create_table_exclusive_item_role(self, ctx) -> None:
        """ Creates the ExclusiveItemRole table in the database. """

        member: discord.Member = ctx.author
        if await self.check_table_exclusive_item_role_exists():
            return await ctx.send(f"**Table `ExclusiveItemRole` already exists, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("""
            CREATE TABLE ExclusiveItemRole (
                role_id BIGINT NOT NULL,
                item_name VARCHAR(30) NOT NULL,
                image_name VARCHAR(50) NOT NULL,
                PRIMARY KEY(role_id, item_name),
                CONSTRAINT fk_eit_image_name FOREIGN KEY (image_name) REFERENCES RegisteredItems (image_name) ON DELETE CASCADE ON UPDATE CASCADE
            ) CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully created the `ExclusiveItemRole` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def drop_table_exclusive_item_role(self, ctx) -> None:
        """ Dropss the ExclusiveItemRole table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_exclusive_item_role_exists():
            return await ctx.send(f"**Table `ExclusiveItemRole` doesn't exist, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DROP TABLE ExclusiveItemRole")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully dropped the `ExclusiveItemRole` table, {member.mention}!**")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def reset_table_exclusive_item_role(self, ctx) -> None:
        """ Resets the ExclusiveItemRole table in the database. """

        member: discord.Member = ctx.author
        if not await self.check_table_exclusive_item_role_exists():
            return await ctx.send(f"**Table `ExclusiveItemRole` doesn't exist yet, {member.mention}!**")

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM ExclusiveItemRole")
        await db.commit()
        await mycursor.close()
        await ctx.send(f"**Successfully reset the `ExclusiveItemRole` table, {member.mention}!**")


    async def check_table_exclusive_item_role_exists(self) -> bool:
        """ Checks whether the ExclusiveItemRole table exists. """

        mycursor, _ = await the_database()
        await mycursor.execute("SHOW TABLE STATUS LIKE 'ExclusiveItemRole'")
        exists = await mycursor.fetchone()
        await mycursor.close()
        if exists:
            return True
        else:
            return False

    async def insert_exclusive_item_role(self, role_id: int, item_name: str, image_name: str) -> None:
        """ Inserts an Exclusive Item Role.
        :param role_id: The exclusive item role ID.
        :param item_name: The name of the item this role has access to.
        :param image_name: The image name of that item."""

        mycursor, db = await the_database()
        await mycursor.execute("""
            INSERT INTO ExclusiveItemRole (
                role_id, item_name, image_name
            ) VALUES (%s, %s, %s)
        """, (role_id, item_name, image_name))
        await db.commit()
        await mycursor.close()

    async def get_exclusive_item_role(self, item_name: str, role_id: int) -> List[Union[int, str]]:
        """ Gets an exclusive item role from an item.
        :param item_name: The name of the item from which to get the role.
        :param role_id: The ID of the role to get. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM ExclusiveItemRole WHERE LOWER(item_name) = LOWER(%s) AND role_id = %s", (item_name, role_id))
        role = await mycursor.fetchone()
        await mycursor.close()
        return role

    async def get_exclusive_item_roles(self, item_name: str) -> List[List[Union[int, str]]]:
        """ Gets all exclusive item roles from an item.
        :param item_name: The name of the item from which to get the roles. """

        mycursor, _ = await the_database()
        await mycursor.execute("SELECT * FROM ExclusiveItemRole WHERE LOWER(item_name) = LOWER(%s)", (item_name,))
        roles = await mycursor.fetchall()
        await mycursor.close()
        return roles

    async def delete_exclusive_item_role(self, item_name: str, role_id: int) -> None:
        """ Deletes an exclusive item role from an item.
        :param item_name: The item name from which to remove the role.
        :param role_id: The ID of the role to remove. """

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM ExclusiveItemRole WHERE LOWER(item_name) = LOWER(%s) AND role_id = %s", (item_name, role_id))
        await db.commit()
        await mycursor.close()

    async def delete_exclusive_item_roles(self, item_name: str) -> None:
        """ Deletes all exclusive item roles from an item.
        :param item_name: The item name from which to remove the roles."""

        mycursor, db = await the_database()
        await mycursor.execute("DELETE FROM ExclusiveItemRole WHERE LOWER(item_name) = LOWER(%s)", (item_name,))
        await db.commit()
        await mycursor.close()