from __future__ import annotations

import discord

from bot.constants import MODE_PRESETS
from bot.ui.modals import QuickAskModal, SystemNoteModal, VoiceSettingsModal, VoiceSpeakModal


class ModeSelect(discord.ui.Select):
    def __init__(self, cog, guild_id: int) -> None:
        options = [
            discord.SelectOption(
                label=preset.label,
                value=preset.key,
                emoji=preset.emoji,
                description=f'Switch to {preset.label} mode.',
            )
            for preset in MODE_PRESETS.values()
        ]
        super().__init__(placeholder='Select a live mode...', min_values=1, max_values=1, options=options)
        self.cog = cog
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This control works only in a server.', ephemeral=True)
            return
        state = self.cog.state.set_mode(self.guild_id, self.values[0])
        self.cog.presence_manager.set_mode(self.values[0])
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id, state_override=state),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )


class ControlCenterView(discord.ui.View):
    def __init__(self, cog, guild_id: int) -> None:
        super().__init__(timeout=900)
        self.cog = cog
        self.guild_id = guild_id
        self.add_item(ModeSelect(cog, guild_id))

    @discord.ui.button(label='Quick Ask', style=discord.ButtonStyle.success, emoji='💬', row=1)
    async def quick_ask(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        mode = self.cog.state.get(self.guild_id).get('mode', 'normal')
        await interaction.response.send_modal(QuickAskModal(self.cog, mode))

    @discord.ui.button(label='Toggle Mentions', style=discord.ButtonStyle.primary, emoji='🎯', row=1)
    async def toggle_mentions(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        state = self.cog.state.toggle_mention(self.guild_id)
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id, state_override=state),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )

    @discord.ui.button(label='Lock/Unlock Here', style=discord.ButtonStyle.secondary, emoji='🔒', row=1)
    async def lock_here(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.channel is None:
            await interaction.response.send_message('Channel not found.', ephemeral=True)
            return
        state = self.cog.state.toggle_channel_lock(self.guild_id, interaction.channel.id)
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id, state_override=state),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )

    @discord.ui.button(label='Voice Hub', style=discord.ButtonStyle.primary, emoji='🎙️', row=1)
    async def voice_hub(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            embed=self.cog.build_voice_hub_embed(self.guild_id),
            files=self.cog.brand_files(),
            ephemeral=True,
            view=self.cog.voice_hub_view(self.guild_id),
        )

    @discord.ui.button(label='Clear Locks', style=discord.ButtonStyle.danger, emoji='🧹', row=2)
    async def clear_locks(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        state = self.cog.state.clear_channel_locks(self.guild_id)
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id, state_override=state),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )

    @discord.ui.button(label='System Note', style=discord.ButtonStyle.secondary, emoji='📝', row=2)
    async def system_note(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(SystemNoteModal(self.cog))

    @discord.ui.button(label='Status', style=discord.ButtonStyle.primary, emoji='📊', row=2)
    async def status(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            embed=self.cog.build_status_embed(self.guild_id),
            files=self.cog.brand_files(),
            ephemeral=True,
        )

    @discord.ui.button(label='Voice Design', style=discord.ButtonStyle.secondary, emoji='🧩', row=2)
    async def voice_design(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            embed=self.cog.build_voice_architecture_embed(self.guild_id),
            files=self.cog.brand_files(),
            ephemeral=True,
        )

    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.secondary, emoji='🔄', row=2)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )


class VoiceHubView(discord.ui.View):
    def __init__(self, cog, guild_id: int) -> None:
        super().__init__(timeout=900)
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.button(label='Join Voice', style=discord.ButtonStyle.success, emoji='🔊', row=0)
    async def join_voice(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_voice_action(interaction, action='join', text=None)

    @discord.ui.button(label='Leave Voice', style=discord.ButtonStyle.danger, emoji='🛑', row=0)
    async def leave_voice(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_voice_action(interaction, action='leave', text=None)

    @discord.ui.button(label='Speak', style=discord.ButtonStyle.primary, emoji='🗣️', row=0)
    async def speak(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(VoiceSpeakModal(self.cog))

    @discord.ui.button(label='Arm Voice', style=discord.ButtonStyle.success, emoji='🎧', row=1)
    async def arm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_voice_arm(interaction)

    @discord.ui.button(label='Disarm', style=discord.ButtonStyle.secondary, emoji='🧯', row=1)
    async def disarm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_voice_disarm(interaction)

    @discord.ui.button(label='Voice Settings', style=discord.ButtonStyle.primary, emoji='⚙️', row=1)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        state = self.cog.state.get(self.guild_id)
        await interaction.response.send_modal(VoiceSettingsModal(self.cog, state))

    @discord.ui.button(label='Architecture', style=discord.ButtonStyle.secondary, emoji='🧠', row=2)
    async def architecture(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            embed=self.cog.build_voice_architecture_embed(self.guild_id),
            files=self.cog.brand_files(),
            ephemeral=True,
        )

    @discord.ui.button(label='Refresh Hub', style=discord.ButtonStyle.secondary, emoji='🔄', row=2)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            embed=self.cog.build_voice_hub_embed(self.guild_id),
            attachments=self.cog.brand_files(),
            view=self.cog.voice_hub_view(self.guild_id),
        )


class InfoLinksView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=300)
        self.add_item(discord.ui.Button(label='OpenRouter', style=discord.ButtonStyle.link, url='https://openrouter.ai/'))
        self.add_item(discord.ui.Button(label='AssemblyAI', style=discord.ButtonStyle.link, url='https://www.assemblyai.com/'))
