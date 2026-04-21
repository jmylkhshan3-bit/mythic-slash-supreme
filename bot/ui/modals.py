from __future__ import annotations

import discord


class SystemNoteModal(discord.ui.Modal, title='Mythic Server Note'):
    note = discord.ui.TextInput(
        label='Server note',
        style=discord.TextStyle.paragraph,
        placeholder='Example: Keep answers concise, professional, and helpful.',
        max_length=600,
        required=False,
    )

    def __init__(self, cog) -> None:
        super().__init__(timeout=300)
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This action works inside a server only.', ephemeral=True)
            return
        state = self.cog.state.set_system_note(interaction.guild.id, str(self.note.value or ''))
        await interaction.response.send_message(
            embed=self.cog.build_status_embed(interaction.guild.id, state_override=state),
            files=self.cog.brand_files(),
            ephemeral=True,
        )


class QuickAskModal(discord.ui.Modal, title='Ask Mythic'):
    prompt = discord.ui.TextInput(
        label='Question',
        style=discord.TextStyle.paragraph,
        placeholder='Ask anything or describe the image/file you want analyzed...',
        max_length=1800,
        required=True,
    )

    def __init__(self, cog, mode: str) -> None:
        super().__init__(timeout=300)
        self.cog = cog
        self.mode = mode

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.cog.run_ai_flow(
            interaction=interaction,
            prompt=str(self.prompt.value),
            mode=self.mode,
        )
