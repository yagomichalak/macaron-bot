import discord
from discord.ext import commands
from typing import List, Optional
from extra import utils

class ReplayAudioView(discord.ui.View):
    """ View for replaying an audio in the game. """

    def __init__(self, client: commands.Bot, timeout: Optional[float] = 28):
        super().__init__(timeout=timeout)
        self.client = client
        self.cog = client.get_cog('Game')

    @discord.ui.button(label="Replay Audio", style=discord.ButtonStyle.success, custom_id="replay_audio_id")
    async def replay_audio_button(self, button: discord.ui.button, interaction: discord.Interaction) -> None:
        """ Callback for the replay audio button click. """

        await interaction.response.defer()

        await self.cog.audio(self.cog.audio_path, self.cog.vc)
        await utils.disable_buttons(self)
        button.label = "Audio Replayed"
        button.style = discord.ButtonStyle.danger
        await interaction.message.edit(view=self)
        await interaction.followup.send("**Replaying audio!**")
        self.stop()