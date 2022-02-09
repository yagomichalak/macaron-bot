import discord
from discord.ext import commands
from typing import List, Union

class ChangeItemCategoryMenuSelect(discord.ui.Select):
    def __init__(self, registered_items: List[List[Union[str, int]]]):
        super().__init__(
            custom_id="item_category_menu_id", placeholder="Change the Item Category.", 
            min_values=1, max_values=1, 
            options=[
                discord.SelectOption(label="All", description="Shows all items.", emoji="🎶"),
                discord.SelectOption(label="backgrounds", description="Shows the backgrounds items.", emoji="🎁"),
            ])

        self.registered_items = registered_items
        self.item_category: str = 'All'
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        option = interaction.data['values'][0]
        self.view.item_category = option
        formatted_items = await self.sort_registered_items(option)
        # Updates the paginator
        self.view.pages = formatted_items
        await self.view.update()


    async def sort_registered_items(self, option = 'All') -> List[str]:
        """ Sorts the registered items. """

        # Filters items
        filtered_items: List[List[Union[str, int]]] = []
        if option != 'All':
            filtered_items = [
                regitem for regitem in self.registered_items 
                if regitem[1] == option
            ]
        else:
            filtered_items = self.registered_items

        # Formats items
        formatted_items = [
            f"**{regitem[2]}**: `{regitem[3]}` crumbs. ({regitem[1]})" for regitem in filtered_items
        ]
        if not formatted_items:
            print('la option', option)
            if option == 'All':
                formatted_items = ['No items registered']
            else:
                formatted_items = [f'No `{option}` items registered']

        # Makes embeds out of the items

        return formatted_items