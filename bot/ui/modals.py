from __future__ import annotations

import discord


class SystemNoteModal(discord.ui.Modal, title='Mythic Server Note'):
    note = discord.ui.TextInput(
        label='Server note',
        style=discord.TextStyle.paragraph,
        placeholder='Example: Answer in Arabic first, keep replies concise, and use bullet points rarely.',
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
        placeholder='Ask anything...',
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


class VoiceSpeakModal(discord.ui.Modal, title='Speak in Voice'):
    text = discord.ui.TextInput(
        label='Text to speak',
        style=discord.TextStyle.paragraph,
        placeholder='Type the text the bot should speak inside voice...',
        max_length=1500,
        required=True,
    )

    def __init__(self, cog) -> None:
        super().__init__(timeout=300)
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.cog.handle_voice_action(interaction, action='speak', text=str(self.text.value))


class VoiceSettingsModal(discord.ui.Modal, title='Official Voice Runtime'):
    wake_phrase = discord.ui.TextInput(
        label='Wake phrase',
        placeholder='hey m',
        default='hey m',
        required=True,
        max_length=40,
    )
    input_language = discord.ui.TextInput(
        label='Input language',
        placeholder='auto / ar / en',
        default='auto',
        required=True,
        max_length=10,
    )
    output_language = discord.ui.TextInput(
        label='Output language',
        placeholder='auto / ar / en',
        default='auto',
        required=True,
        max_length=10,
    )
    silence_seconds = discord.ui.TextInput(
        label='Silence seconds',
        placeholder='2.0',
        default='2.0',
        required=True,
        max_length=8,
    )

    def __init__(self, cog, state: dict) -> None:
        super().__init__(timeout=300)
        self.cog = cog
        self.wake_phrase.default = str(state.get('voice_wake_phrase', 'hey m'))
        self.input_language.default = str(state.get('voice_input_language', 'auto'))
        self.output_language.default = str(state.get('voice_output_language', 'auto'))
        self.silence_seconds.default = str(state.get('voice_silence_seconds', 2.0))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This action works inside a server only.', ephemeral=True)
            return
        try:
            silence = float(str(self.silence_seconds.value).strip())
        except ValueError:
            await interaction.response.send_message('Silence seconds must be a number like 2.0.', ephemeral=True)
            return
        state = self.cog.state.set_voice_profile(
            interaction.guild.id,
            wake_phrase=str(self.wake_phrase.value),
            input_language=str(self.input_language.value),
            output_language=str(self.output_language.value),
            silence_seconds=silence,
        )
        await interaction.response.send_message(
            embed=self.cog.build_voice_hub_embed(interaction.guild.id, state_override=state),
            files=self.cog.brand_files(),
            ephemeral=True,
            view=self.cog.voice_hub_view(interaction.guild.id),
        )
