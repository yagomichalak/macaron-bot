import discord
from discord.ext import commands
from typing import List, Union, Optional

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
        self.crumbs_emoji: str = '<:crumbs:940086555224211486>'
        self.croutons_emoji: str = '<:croutons:945013460041891891>'
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        option = interaction.data['values'][0]
        self.view.item_category = option
        formatted_items = await self.sort_registered_items(option)
        # Updates the paginator

        await self.view.update(pages=formatted_items)
        await interaction.edit_original_message(view=self.view)


    async def sort_registered_items(self, option = 'All', exclusive: Optional[bool] = False, hidden: Optional[bool] = False) -> List[str]:
        """ Sorts the registered items.
        :param exclusive: Whether to show exclusive items. [Optional][Default = False] 
        :param hidden: Whether to show hidden items. [Optional][Default = False] """

        exclusive = 1 if exclusive else 0

        # Filters items
        filtered_items: List[List[Union[str, int]]] = []
        if option != 'All':
            filtered_items = [
                regitem for regitem in self.registered_items 
                if regitem[1] == option
            ]
        else:
            filtered_items = self.registered_items

        # Filter exclusive / not exclusive items
        if hidden:
            filtered_items = list(filter(lambda item: item[7], filtered_items))
        else:
            filtered_items = list(filter(
                lambda item: item[6] == exclusive and not item[7], filtered_items))

        emoji = self.crumbs_emoji if not exclusive else self.croutons_emoji

        # Formats items
        formatted_items = [
            f"**{regitem[2]}**: {emoji} `{regitem[3]}` ({regitem[1]})"
            for regitem in filtered_items
        ]
        if not formatted_items:
            if option == 'All':
                formatted_items = ['No items registered']
            else:
                formatted_items = [f'No `{option}` items registered']

        # Makes embeds out of the items
        embedded_items: List[discord.Embed] = []
        text_embed: discord.Embed = discord.Embed(
            title=f"__Showing `{option}` items__",
            color=discord.Color.green() if not exclusive else int('000001', 16)
        )

        per_page: int = 10
        counter: int = 0

        for _ in range(len(formatted_items)):
            indexed_items: List[str] = []

            for ii in range(per_page):
                if len(formatted_items) < counter + ii + 1:
                    break
                indexed_items.append(formatted_items[counter+ii])

            if not indexed_items:
                break

            counter += per_page
            index_embed = text_embed.copy()
            index_embed.description = '\n'.join(indexed_items)
            embedded_items.append(index_embed)
            indexed_items.clear()
        
        return embedded_items