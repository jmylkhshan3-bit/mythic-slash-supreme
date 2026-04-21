from __future__ import annotations

import discord

from bot.constants import MODE_PRESETS
from bot.ui.modals import QuickAskModal, SystemNoteModal


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

    @discord.ui.button(label='AFK Join', style=discord.ButtonStyle.primary, emoji='🌙', row=1)
    async def afk_join(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_voice_afk(interaction)

    @discord.ui.button(label='Leave Voice', style=discord.ButtonStyle.danger, emoji='📴', row=1)
    async def leave_voice(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self.cog.handle_voice_leave(interaction)

    @discord.ui.button(label='Vision Tips', style=discord.ButtonStyle.secondary, emoji='🖼️', row=2)
    async def vision_tips(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            embed=self.cog.build_vision_embed(self.guild_id),
            files=self.cog.brand_files(),
            ephemeral=True,
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

    @discord.ui.button(label='Gallery', style=discord.ButtonStyle.secondary, emoji='🧩', row=3)
    async def gallery(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message(
            embed=self.cog.build_gallery_embed(self.guild_id),
            files=self.cog.brand_files(),
            ephemeral=True,
        )

    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.secondary, emoji='🔄', row=3)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )


class InfoLinksView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=900)
        self.add_item(discord.ui.Button(label='OpenRouter', url='https://openrouter.ai'))
        self.add_item(discord.ui.Button(label='Discord Developer Portal', url='https://discord.com/developers/applications'))
