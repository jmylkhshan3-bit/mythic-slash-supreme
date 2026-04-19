from __future__ import annotations

import asyncio
import logging
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from bot.constants import MODE_CHOICES, MODE_PRESETS, PROGRESS_STEPS, SPINNER_FRAMES
from bot.ui.embeds import (
    about_embed,
    apply_branding,
    help_embed,
    info_embed,
    loading_embed,
    locks_embed,
    panel_embed,
    ping_embed,
    profile_embed,
    response_embed,
    scene_embed,
    status_embed,
)
from bot.ui.views import ControlCenterView, InfoLinksView

log = logging.getLogger(__name__)


class MythicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = bot.state_manager
        self.ai = bot.openrouter_client
        self.assets = bot.asset_manager
        self.presence_manager = bot.presence_manager

    def brand_files(self) -> list[discord.File]:
        files: list[discord.File] = []
        banner = self.assets.banner_file()
        avatar = self.assets.avatar_file()
        if banner:
            files.append(banner)
        if avatar:
            files.append(avatar)
        return files

    def build_status_embed(self, guild_id: int, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = status_embed(snapshot, snapshot.get('mode', 'normal'), self.assets.asset_status(), self.bot.settings.openrouter_model)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_panel_embed(self, guild_id: int, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = panel_embed(snapshot, snapshot.get('mode', 'normal'))
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_info_embed(self, mode: str) -> discord.Embed:
        embed = info_embed(mode, self.bot.settings.openrouter_model, len(self.assets.icon_names()))
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_profile_embed(self, mode: str) -> discord.Embed:
        embed = profile_embed(mode, self.assets.asset_status(), self.assets.icon_names())
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_help_embed(self, mode: str) -> discord.Embed:
        embed = help_embed(mode)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_about_embed(self, guild_id: int) -> discord.Embed:
        snapshot = self.state.get(guild_id)
        embed = about_embed(snapshot.get('mode', 'normal'), snapshot.get('mention_enabled', True))
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_scene_embed(self, mode: str, lines: list[str], presence_lines: list[str]) -> discord.Embed:
        embed = scene_embed(mode, lines, presence_lines)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    async def animate_response(self, *, send_callback, edit_callback, prompt: str, mode: str, user_name: str, guild_name: str | None, system_note: str) -> None:
        preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
        files = self.brand_files()
        loading_message = await send_callback(
            embed=loading_embed(mode, SPINNER_FRAMES[0], preset.loading_lines[0], prompt, user_name, 1),
            files=files,
        )
        start = time.perf_counter()
        task = asyncio.create_task(
            self.ai.chat(
                prompt=prompt,
                mode=mode,
                user_name=user_name,
                guild_name=guild_name,
                system_note=system_note,
            )
        )
        tick = 1
        while not task.done():
            await asyncio.sleep(0.9)
            line = preset.loading_lines[tick % len(preset.loading_lines)]
            frame = SPINNER_FRAMES[tick % len(SPINNER_FRAMES)]
            step = min(PROGRESS_STEPS, 1 + (tick % PROGRESS_STEPS))
            tick += 1
            try:
                await edit_callback(
                    loading_message,
                    embed=loading_embed(mode, frame, line, prompt, user_name, step),
                    attachments=self.brand_files(),
                )
            except discord.HTTPException:
                pass
        try:
            answer = await task
        except Exception as exc:
            log.exception('AI request failed')
            answer = f'AI request failed: {exc}'
        elapsed = time.perf_counter() - start
        final_embed = response_embed(mode, prompt, answer, user_name, elapsed)
        apply_branding(final_embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await edit_callback(loading_message, embed=final_embed, attachments=self.brand_files())

    async def run_ai_flow(self, interaction: discord.Interaction, prompt: str, mode: str | None = None) -> None:
        chosen_mode = mode or self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True)
        await self.animate_response(
            send_callback=lambda **kwargs: interaction.followup.send(wait=True, **kwargs),
            edit_callback=lambda msg, **kwargs: msg.edit(**kwargs),
            prompt=prompt,
            mode=chosen_mode,
            user_name=interaction.user.display_name,
            guild_name=interaction.guild.name if interaction.guild else None,
            system_note=self.state.get(interaction.guild.id if interaction.guild else None).get('system_note', ''),
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.bot.settings.enable_mention_reply:
            return
        if message.author.bot or self.bot.user is None or message.guild is None:
            return
        if self.bot.user not in message.mentions or message.mention_everyone:
            return
        snapshot = self.state.get(message.guild.id)
        if not snapshot.get('mention_enabled', True):
            return
        allowed = snapshot.get('allowed_channel_ids', [])
        if allowed and message.channel.id not in allowed:
            return
        prompt = message.content.replace(self.bot.user.mention, '').strip()
        if not prompt:
            await message.reply(
                embed=self.build_panel_embed(message.guild.id),
                view=ControlCenterView(self, message.guild.id),
                files=self.brand_files(),
            )
            return
        async with message.channel.typing():
            await self.animate_response(
                send_callback=lambda **kwargs: message.reply(**kwargs),
                edit_callback=lambda msg, **kwargs: msg.edit(**kwargs),
                prompt=prompt,
                mode=snapshot.get('mode', 'normal'),
                user_name=message.author.display_name,
                guild_name=message.guild.name,
                system_note=snapshot.get('system_note', ''),
            )

    @app_commands.command(name='ask', description='Ask the AI using slash commands only.')
    @app_commands.describe(prompt='Your question for the bot', mode='Optional temporary mode override for this request')
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def ask(self, interaction: discord.Interaction, prompt: str, mode: app_commands.Choice[str] | None = None) -> None:
        await self.run_ai_flow(interaction, prompt, mode.value if mode else None)

    @app_commands.command(name='mode', description='Change the live server mode for everyone.')
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        state = self.state.set_mode(interaction.guild.id, mode.value)
        self.presence_manager.set_mode(mode.value)
        await interaction.response.send_message(
            embed=self.build_status_embed(interaction.guild.id, state_override=state),
            files=self.brand_files(),
        )

    @app_commands.command(name='setup', description='Open the legendary slash dashboard.')
    async def setup(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.send_message(
            embed=self.build_panel_embed(interaction.guild.id),
            view=ControlCenterView(self, interaction.guild.id),
            files=self.brand_files(),
        )

    @app_commands.command(name='panel', description='Open the command center panel again.')
    async def panel(self, interaction: discord.Interaction) -> None:
        await self.setup(interaction)

    @app_commands.command(name='status', description='Inspect runtime state and asset health.')
    async def status(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.send_message(
            embed=self.build_status_embed(interaction.guild.id),
            files=self.brand_files(),
            ephemeral=True,
        )

    @app_commands.command(name='info', description='Show build info and resource links.')
    async def info(self, interaction: discord.Interaction) -> None:
        mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        await interaction.response.send_message(
            embed=self.build_info_embed(mode),
            view=InfoLinksView(),
            files=self.brand_files(),
        )

    @app_commands.command(name='help', description='Show the slash command deck.')
    async def help(self, interaction: discord.Interaction) -> None:
        mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        await interaction.response.send_message(embed=self.build_help_embed(mode), files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='systemnote', description='Set or clear the server system note.')
    @app_commands.describe(note='Leave empty to clear the note')
    async def systemnote(self, interaction: discord.Interaction, note: str = '') -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        state = self.state.set_system_note(interaction.guild.id, note)
        await interaction.response.send_message(
            embed=self.build_status_embed(interaction.guild.id, state_override=state),
            files=self.brand_files(),
            ephemeral=True,
        )

    @app_commands.command(name='settings', description='Open the modal to edit the server note.')
    async def settings(self, interaction: discord.Interaction) -> None:
        from bot.ui.modals import SystemNoteModal
        await interaction.response.send_modal(SystemNoteModal(self))

    @app_commands.command(name='profile', description='Show branding assets and icon preview.')
    async def profile(self, interaction: discord.Interaction) -> None:
        mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        await interaction.response.send_message(embed=self.build_profile_embed(mode), files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='scene', description="Preview a mode's animated text lines.")
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def scene(self, interaction: discord.Interaction, mode: app_commands.Choice[str] | None = None) -> None:
        mode_key = mode.value if mode else self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        preset = MODE_PRESETS.get(mode_key, MODE_PRESETS['normal'])
        sample_loading = random.sample(preset.loading_lines, k=min(8, len(preset.loading_lines)))
        sample_presence = random.sample(preset.presence_lines, k=min(8, len(preset.presence_lines)))
        await interaction.response.send_message(
            embed=self.build_scene_embed(mode_key, sample_loading, sample_presence),
            files=self.brand_files(),
            ephemeral=True,
        )

    @app_commands.command(name='about', description='Show build summary and deployment notes.')
    async def about(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id if interaction.guild else None
        mode = self.state.get(guild_id).get('mode', 'normal')
        embed = self.build_about_embed(guild_id or 0)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='ping', description='Check Discord gateway and AI readiness.')
    async def ping(self, interaction: discord.Interaction) -> None:
        mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        gateway_ms = round(self.bot.latency * 1000)
        embed = ping_embed(mode, gateway_ms, None)
        apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='locks', description='List the current mention channel locks.')
    async def locks(self, interaction: discord.Interaction) -> None:
        mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        channel_ids = self.state.get(interaction.guild.id if interaction.guild else None).get('allowed_channel_ids', [])
        embed = locks_embed(mode, channel_ids)
        apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MythicCog(bot))
