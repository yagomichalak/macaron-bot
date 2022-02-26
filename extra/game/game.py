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

    def clean_word(self, word: str, symbols: Optional[List[str]] = None) -> str:
        """ Cleans a word by removing a series of symbols.
        :param word: The word to clean.
        :param symbols: The list of symbols to remove. [Optional] """

        if not symbols:
            symbols = ['*', '~']

        for symbol in symbols:
            word.replace(symbol, '')

        return word

    def intelindex(self, search_word: str, sentence: str, percentage: int = 89) -> int:
        """ Intelligent index; Gets the index of the given word in a given sentence, if any,
        and the percentage ratio of the word similarity.
        :param search_word: The word to search in the text.
        :param sentence: The text to in which to look for the word.
        :param percentage: The percentage of similarity to on which to base the search. [Default = 89] """

        index: int = None
        ratio: str = 0
        for i, word in enumerate(sentence):

            ratio = fuzz.ratio(search_word.lower(), word.lower())
            if ratio >= percentage:
                index = i
                break

        return index, ratio

    def highlight_answer(self, user_answer: str, correct_answer: str) -> str:
        """ Highlights words in the user answer that are different from the correct answer.
        :param user_answer: The user answer.
        :param correct_answer: The correct answer. """

        # user_answer: List[str] = user_answer.split()
        # user_answer: List[str] = correct_answer.split()

        lca, lua = len(correct_answer), len(user_answer)
        longest_answer_length = lca if lca > lua else lua
        highlighted_answer_list: list[str] = []

        # Loops based on the longest answer
        for indx in range(longest_answer_length):

            user_word: str = None
            if indx < lua:
                user_word = user_answer[indx]

            word_index: int = None
            ratio: int = 0
            if user_word:
                word_index, ratio = self.intelindex(user_word, correct_answer)

            if word_index is not None:
                uword = user_word
                if 100 > ratio >= 89:
                    uword = f"**{uword}**"
                highlighted_answer_list.append(uword)
            else:
                if lca > lua:
                    if lua > indx:
                        highlighted_answer_list.append(f"~~`{user_answer[indx]}`~~")
                elif lca <= lua:
                    highlighted_answer_list.append(f"~~`{user_word}`~~")

        # If correct answer is longer than the user answer
        # Appends correct words from the correct answer to the highlighted answer
        if len(highlighted_answer_list) < lca:
            new_hl: list[str] = []
            for bw in correct_answer:
                for aw in highlighted_answer_list:
                    ratio = fuzz.ratio(self.clean_word(aw.lower()), bw.lower())
                    if ratio >= 89:
                        new_hl.append(aw)
                        break
                else:
                    new_hl.append(f"~~`{bw}`~~")

            highlighted_answer_list = new_hl

        # Returns the new generated highlighted answer
        return ' '.join(highlighted_answer_list)

