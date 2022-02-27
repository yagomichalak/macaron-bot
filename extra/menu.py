from discord.ext import menus

class SwitchPages(menus.ListPageSource):
	""" A class for switching pages. """

	def __init__(self, data, **kwargs):
		""" Class init method. """

		super().__init__(data, per_page=10)
		self.change_embed = kwargs.get('change_embed')
		self.kwargs = kwargs


	async def format_page(self, menu, entries):
		""" Formats each page. """

		offset = menu.current_page * self.per_page
		return await self.change_embed(
			ctx=menu.ctx, entries=entries, offset=offset+1, lentries=len(self.entries), kwargs=self.kwargs
			)