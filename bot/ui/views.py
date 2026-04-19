from __future__ import annotations

import random

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
        super().__init__(placeholder='Select a live mode...', min_values=1, max_values=1, options=options, row=0)
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


class QuickActionSelect(discord.ui.Select):
    def __init__(self, cog, guild_id: int) -> None:
        options = [
            discord.SelectOption(label='Status', value='status', emoji='📊', description='Open the status wall'),
            discord.SelectOption(label='Profile', value='profile', emoji='🖼️', description='Open brand and icon info'),
            discord.SelectOption(label='Help', value='help', emoji='❓', description='Show command deck'),
            discord.SelectOption(label='About', value='about', emoji='✨', description='Show build summary'),
            discord.SelectOption(label='Scene', value='scene', emoji='🎬', description='Preview mode animation lines'),
        ]
        super().__init__(placeholder='Open a quick card...', min_values=1, max_values=1, options=options, row=3)
        self.cog = cog
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction) -> None:
        mode = self.cog.state.get(self.guild_id).get('mode', 'normal')
        value = self.values[0]
        if value == 'status':
            embed = self.cog.build_status_embed(self.guild_id)
        elif value == 'profile':
            embed = self.cog.build_profile_embed(mode)
        elif value == 'help':
            embed = self.cog.build_help_embed(mode)
        elif value == 'about':
            embed = self.cog.build_about_embed(self.guild_id)
        else:
            preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
            embed = self.cog.build_scene_embed(mode, random.sample(preset.loading_lines, k=8), random.sample(preset.presence_lines, k=8))
        await interaction.response.send_message(embed=embed, files=self.cog.brand_files(), ephemeral=True)


class ControlCenterView(discord.ui.View):
    def __init__(self, cog, guild_id: int) -> None:
        super().__init__(timeout=900)
        self.cog = cog
        self.guild_id = guild_id
        self.add_item(ModeSelect(cog, guild_id))
        self.add_item(QuickActionSelect(cog, guild_id))

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

    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.secondary, emoji='🔄', row=2)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            embed=self.cog.build_panel_embed(self.guild_id),
            view=ControlCenterView(self.cog, self.guild_id),
            attachments=self.cog.brand_files(),
        )


class InfoLinksView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=300)
        self.add_item(discord.ui.Button(label='OpenRouter', style=discord.ButtonStyle.link, url='https://openrouter.ai/'))
        self.add_item(discord.ui.Button(label='discord.py', style=discord.ButtonStyle.link, url='https://discordpy.readthedocs.io/'))
        self.add_item(discord.ui.Button(label='Discord Dev Portal', style=discord.ButtonStyle.link, url='https://discord.com/developers/applications'))
