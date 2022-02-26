import discord
from discord.ext import commands
from typing import List, Tuple, Optional, Union
from fuzzywuzzy import fuzz
import string
import random

class GameSystem(commands.Cog):
    """ Class for the game logic system. """

    def __init__(self, client: commands.Bot) -> None:
        """ Class init method. """

        self.client = client

    async def compare_answers(self, player_answer: str, real_answer: str) -> int:
        """ Compares the player answer with the actual answer, and gives an
        accuracy percentage value.
        :param player: The player answer:
        :param real_answer: The real answer. """

        variants: Tuple[str] = ('.', ';', ':', ',', '!', '?')

        if player_answer.endswith(variants):
            player_answer = player_answer[:-1]

        if real_answer.endswith(variants):
            real_answer = real_answer[:-1]

        return fuzz.ratio(player_answer.lower(), real_answer.lower())

    def generate_session_id(self, length: Optional[int] = 18) -> str:
        """ Generates a session ID.
        :param length: The length of the session ID. [Default = 18] """

        # Defines data
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        num = string.digits
        symbols = string.punctuation

        # Combines the data
        all = lower + upper + num + symbols

        # Uses random 
        temp = random.sample(all,length)

        # Create the session ID 
        session_id = "".join(temp)
        return session_id
    