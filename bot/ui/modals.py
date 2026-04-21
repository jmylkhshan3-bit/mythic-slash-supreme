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


class SpeakModal(discord.ui.Modal, title='Speak with Mythic'):
    text = discord.ui.TextInput(
        label='Text to speak',
        style=discord.TextStyle.paragraph,
        placeholder='Type what the bot should say in voice...',
        max_length=1500,
        required=True,
    )

    def __init__(self, cog) -> None:
        super().__init__(timeout=300)
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.cog.handle_speak(interaction, str(self.text.value))


class VoiceSettingsModal(discord.ui.Modal, title='Voice Capture Settings'):
    wake_phrase = discord.ui.TextInput(
        label='Wake phrase',
        placeholder='hey m',
        default='hey m',
        required=True,
        max_length=40,
    )
    input_language = discord.ui.TextInput(
        label='Input language',
        placeholder='auto / en / ar',
        default='auto',
        required=True,
        max_length=10,
    )
    output_language = discord.ui.TextInput(
        label='Reply language',
        placeholder='auto / en / ar',
        default='auto',
        required=True,
        max_length=10,
    )
    silence_seconds = discord.ui.TextInput(
        label='Silence seconds',
        placeholder='5.0',
        default='5.0',
        required=True,
        max_length=8,
    )
    trigger_level = discord.ui.TextInput(
        label='Trigger level dB',
        placeholder='-55.0',
        default='-55.0',
        required=True,
        max_length=8,
    )

    def __init__(self, cog, state: dict) -> None:
        super().__init__(timeout=300)
        self.cog = cog
        self.wake_phrase.default = str(state.get('voice_wake_phrase', 'hey m'))
        self.input_language.default = str(state.get('voice_input_language', 'auto'))
        self.output_language.default = str(state.get('voice_output_language', 'auto'))
        self.silence_seconds.default = str(state.get('voice_silence_seconds', 5.0))
        self.trigger_level.default = str(state.get('voice_trigger_level_db', -55.0))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This action works inside a server only.', ephemeral=True)
            return
        try:
            silence = float(str(self.silence_seconds.value).strip())
            trigger_level = float(str(self.trigger_level.value).strip())
        except ValueError:
            await interaction.response.send_message('Silence seconds and trigger level must be numeric values.', ephemeral=True)
            return
        state = self.cog.state.set_voice_profile(
            interaction.guild.id,
            wake_phrase=str(self.wake_phrase.value),
            input_language=str(self.input_language.value),
            output_language=str(self.output_language.value),
            silence_seconds=silence,
            trigger_level_db=trigger_level,
        )
        await interaction.response.send_message(
            embed=self.cog.build_status_embed(interaction.guild.id, state_override=state),
            files=self.cog.brand_files(),
            ephemeral=True,
        )
