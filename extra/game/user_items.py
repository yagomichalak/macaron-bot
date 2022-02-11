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
    async def _show_registered_items_slash_command(self, ctx,
        item_category: Option(str, name="item_category", description="The item category to show.", choices=[
            'accessories_1', 'accessories_2', 'backgrounds', 'bb_base', 'dual_hands', 'effects', 'eyes', 
            'face_furniture', 'facial_hair', 'hats', 'left_hands', 'mouths', 'right_hands', 'outfits'
        ], required=False, default='All')) -> None:
        """ Shows all the registered items. """

        await ctx.defer()
        member: discord.Member = ctx.author
        registered_items = await self.get_registered_items_ordered_by_price()

        self.pages = registered_items
        view = discord.ui.View()
        select = ChangeItemCategoryMenuSelect(registered_items)
        formatted_items = await select.sort_registered_items(item_category)
        # view.add_item(select)

        paginator = pages.Paginator(pages=formatted_items, custom_view=view)
        await paginator.respond(ctx.interaction, ephemeral=False)

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
            background = Image.open(await self.get_user_specific_item_type(member.id, 'backgrounds')).convert('RGBA')
            bb_base = Image.open(await self.get_user_specific_item_type(member.id, 'bb_base')).convert('RGBA')
            eyes = Image.open(await self.get_user_specific_item_type(member.id, 'eyes')).convert('RGBA')
            mouths = Image.open(await self.get_user_specific_item_type(member.id, 'mouths')).convert('RGBA')
            facil_hair = Image.open(await self.get_user_specific_item_type(member.id, 'facial_hair')).convert('RGBA')
            face_furniture = Image.open(await self.get_user_specific_item_type(member.id, 'face_furniture')).convert('RGBA')
            hats = Image.open(await self.get_user_specific_item_type(member.id, 'hats')).convert('RGBA')
            left_hands = Image.open(await self.get_user_specific_item_type(member.id, 'left_hands')).convert('RGBA')
            right_hands = Image.open(await self.get_user_specific_item_type(member.id, 'right_hands')).convert('RGBA')
            accessories_1 = Image.open(await self.get_user_specific_item_type(member.id, 'accessories_1')).convert('RGBA')
            accessories_2 = Image.open(await self.get_user_specific_item_type(member.id, 'accessories_2')).convert('RGBA')
            effects = Image.open(await self.get_user_specific_item_type(member.id, 'effects')).convert('RGBA')
            outfits = Image.open(await self.get_user_specific_item_type(member.id, 'outfits')).convert('RGBA')
            dual_hands = Image.open(await self.get_user_specific_item_type(member.id, 'dual_hands')).convert('RGBA')
            
            # Gets the user's hidden item categories.
            all_hidden_icats = await self.get_hidden_item_categories(member.id)
            hidden_icats = list(map(lambda ic: ic[1], all_hidden_icats))

            # Pastes all item images
            if not 'bb_base' in hidden_icats: background.paste(bb_base, (0, 0), bb_base)
            if not 'eyes' in hidden_icats: background.paste(eyes, (0, 0), eyes)
            if not 'facil_hair' in hidden_icats: background.paste(facil_hair, (0, 0), facil_hair)
            if not 'mouths' in hidden_icats: background.paste(mouths, (0, 0), mouths)
            if not 'face_furniture' in hidden_icats: background.paste(face_furniture, (0, 0), face_furniture)
            if not 'hats' in hidden_icats: background.paste(hats, (0, 0), hats)
            if not 'left_hands' in hidden_icats: background.paste(left_hands, (0, 0), left_hands)
            if not 'right_hands' in hidden_icats: background.paste(right_hands, (0, 0), right_hands)
            if not 'accessories_1' in hidden_icats: background.paste(accessories_1, (0, 0), accessories_1)
            if not 'accessories_2' in hidden_icats: background.paste(accessories_2, (0, 0), accessories_2)
            if not 'effects' in hidden_icats: background.paste(effects, (0, 0), effects)
            if not 'outfits' in hidden_icats: background.paste(outfits, (0, 0), outfits)
            if not 'dual_hands' in hidden_icats: background.paste(dual_hands, (0, 0), dual_hands)

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

        if not await self.get_user_item(member.id, item_name):
            return await ctx.send(f"**You don't have this item, {member.mention}!**")

        if await self.check_user_can_change_item_state(member.id, item_name):
            return await ctx.send(f"**This item is already unequipped, {member.mention}!**")

        await self.update_item_equipped(member.id, item_name)
        await ctx.send(f"**{member.mention} unequipped __{item_name.title()}__!**")

    async def check_user_can_change_item_state(self, user_id: int, item_name: str, enable: bool = False) -> bool:
        """ Checks whether a user can equip or unequip a specific item.
        :param user_id: The ID of the user to check.
        :param item_name: The name of the item.
        :param enable: Whether to check if you can equip or unequip. """

        mycursor, _ = await the_database()
        enable = 1 if enable else 0
        await mycursor.execute(
            "SELECT * FROM UserItems WHERE user_id = %s AND LOWER(item_name) = LOWER(%s) AND enable = %s", (user_id, item_name, enable))
        item = await mycursor.fetchone()
        await mycursor.close()

        if item:
            return True
        else:
            return False


    @commands.command(aliases=["give_member_item"])
    @commands.has_permissions(administrator=True)
    async def add_member_item(self, ctx, member: discord.Member = None, *, item_name: str = None) -> None:
        """ (ADM) Gives an item to a member.
        :param member: The member to give the item.
        :param item_name: The name of the item. """

        item_name = escape_mentions(item_name)

        if not member:
            return await ctx.send("**Inform a member!**")

        if not item_name:
            return await ctx.send("**Inform an item to add!**")

        if await self.get_user_item(member.id, item_name):
            return await ctx.send(f"**{member.name} already has that item!**")

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {ctx.author.mention}!**")

        await self.insert_user_item(member.id, regitem[2], regitem[1], regitem[0])
        return await ctx.send(f"**Successfully given `{regitem[2].title()}` to {member.name}!**")

    @commands.command(aliases=["delete_member_item"])
    @commands.has_permissions(administrator=True)
    async def remove_member_item(self, ctx, member: discord.Member = None, *, item_name: str = None) -> None:
        """ (ADM) Gives an item to a member.
        :param member: The member to give the item.
        :param item_name: The name of the item. """

        item_name = escape_mentions(item_name)

        if not member:
            return await ctx.send("**Inform a member!**")

        if not item_name:
            return await ctx.send("**Inform an item to add!**")

        if not await self.get_user_item(member.id, item_name):
            return await ctx.send(f"**{member.name} doesn't even have that item!**")

        if not (regitem := await self.get_registered_item(name=item_name)):
            return await ctx.send(f"**This item doesn't exist, {ctx.author.mention}!**")

        await self.delete_user_item(member.id, regitem[2])
        return await ctx.send(f"**Successfully given `{regitem[2].title()}` to {member.name}!**")

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
        await ctx.send(f"**Added `{amount}` curbs to {member.mention}!**")


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
        item_category = escape_mentions(item_category)
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
        await mycursor.execute("DROP HiddenItemCategory")
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