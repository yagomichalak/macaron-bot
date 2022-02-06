import discord
from discord.ext import commands
from external_cons import the_database
import os
from typing import List, Optional, Any, Union


class UserItemsTable(commands.Cog):
    """ Class for managing the UserItems table in the database. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

class UserItemsSystem(commands.Cog):
    """ Class for UserItems system. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client
