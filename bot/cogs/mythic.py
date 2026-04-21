from __future__ import annotations

import asyncio
import logging
import random
import zipfile
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from bot.constants import MODE_CHOICES, MODE_PRESETS
from bot.ui.embeds import (
    apply_branding,
    gallery_embed,
    help_embed,
    info_embed,
    loading_embed,
    panel_embed,
    response_embed,
    status_embed,
    transcript_embed,
)
from bot.ui.views import ControlCenterView, InfoLinksView

log = logging.getLogger(__name__)

TEXT_SUFFIXES = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.yml', '.yaml', '.html', '.css', '.sql', '.csv'}
AUDIO_SUFFIXES = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.mp4', '.mov', '.webm'}


class MythicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = bot.state_manager
        self.ai = bot.openrouter_client
        self.assets = bot.asset_manager
        self.presence_manager = bot.presence_manager
        self.voice_runtime = bot.voice_runtime
        self.elevenlabs = bot.elevenlabs_client

    def brand_files(self) -> list[discord.File]:
        files: list[discord.File] = []
        banner = self.assets.banner_file()
        avatar = self.assets.avatar_file()
        if banner:
            files.append(banner)
        if avatar:
            files.append(avatar)
        return files

    def build_status_embed(self, guild_id: int | None, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = status_embed(snapshot, snapshot.get('mode', 'normal'), self.assets.asset_status(), self.bot.settings.openrouter_model)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_panel_embed(self, guild_id: int, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = panel_embed(snapshot, snapshot.get('mode', 'normal'), self.bot.settings.activation_phrase)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_info_embed(self, mode: str) -> discord.Embed:
        embed = info_embed(mode, self.bot.settings.openrouter_model, len(self.assets.icon_names()))
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_gallery_embed(self, guild_id: int | None) -> discord.Embed:
        mode = self.state.get(guild_id).get('mode', 'normal')
        embed = gallery_embed(mode, self.assets.icon_names())
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    async def _send_setup_panel(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.send_message(
            embed=self.build_panel_embed(interaction.guild.id),
            view=ControlCenterView(self, interaction.guild.id),
            files=self.brand_files(),
        )

    async def animate_response(
        self,
        *,
        send_callback,
        edit_callback,
        prompt: str,
        mode: str,
        user_name: str,
        guild_name: str | None,
        system_note: str,
        attachment_context: str = '',
        image_urls: list[str] | None = None,
    ) -> None:
        preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
        files = self.brand_files()
        loading_message = await send_callback(embed=loading_embed(mode, random.choice(preset.loading_lines), prompt, user_name), files=files)
        try:
            answer = await self.ai.chat(
                prompt=prompt,
                mode=mode,
                user_name=user_name,
                guild_name=guild_name,
                system_note=system_note,
                attachment_context=attachment_context,
                image_urls=image_urls or [],
            )
        except Exception as exc:
            log.exception('AI request failed')
            answer = f'AI request failed: {exc}'
        final_embed = response_embed(mode, prompt, answer, user_name)
        apply_branding(final_embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await edit_callback(loading_message, embed=final_embed, attachments=self.brand_files())

    async def run_ai_flow(
        self,
        interaction: discord.Interaction,
        prompt: str,
        mode: str | None = None,
        attachment_context: str = '',
        image_urls: list[str] | None = None,
    ) -> None:
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
            attachment_context=attachment_context,
            image_urls=image_urls or [],
        )

    async def _extract_attachment_context(self, attachments: list[discord.Attachment]) -> tuple[str, list[str]]:
        if not attachments:
            return '', []
        chunks: list[str] = []
        image_urls: list[str] = []
        for attachment in attachments[:4]:
            suffix = Path(attachment.filename).suffix.lower()
            content_type = (attachment.content_type or '').lower()
            chunks.append(f'Attachment: {attachment.filename} ({content_type or "unknown"})')
            if suffix in TEXT_SUFFIXES or content_type.startswith('text/'):
                try:
                    raw = await attachment.read()
                    text = raw.decode('utf-8', errors='ignore')
                except Exception as exc:
                    text = f'Failed to read text attachment: {exc}'
                if text:
                    chunks.append(text[:6000])
                continue
            if suffix == '.zip':
                try:
                    import io
                    raw = await attachment.read()
                    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                        names = '\n'.join(zf.namelist()[:80])
                    chunks.append('ZIP file entries:\n' + names)
                except Exception as exc:
                    chunks.append(f'Failed to inspect ZIP: {exc}')
                continue
            if suffix in AUDIO_SUFFIXES or content_type.startswith('audio/') or content_type.startswith('video/'):
                if not self.elevenlabs.enabled:
                    chunks.append('Audio/video attachment detected, but ELEVENLABS_API_KEY is missing.')
                    continue
                try:
                    raw = await attachment.read()
                    result = await self.elevenlabs.speech_to_text(data=raw, filename=attachment.filename)
                    chunks.append('Transcription:\n' + (result.text or '[no speech detected]'))
                except Exception as exc:
                    chunks.append(f'Failed to transcribe audio: {exc}')
                continue
            if content_type.startswith('image/'):
                image_urls.append(attachment.url)
                chunks.append('Image attachment detected. Inspect the image content directly and answer using visible details.')
                continue
            chunks.append('Unsupported attachment type for deep parsing in this build.')
        return '\n\n'.join(chunks)[:12000], image_urls

    async def handle_voice_join(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            vc = await self.voice_runtime.connect_or_move(interaction)
            channel_name = getattr(vc.channel, 'name', 'voice') if getattr(vc, 'channel', None) else 'voice'
            await interaction.followup.send(
                f'Joined **{channel_name}**.',
                embed=self.build_status_embed(interaction.guild.id if interaction.guild else None),
                files=self.brand_files(),
                ephemeral=True,
            )
        except Exception as exc:
            log.exception('Voice join failed')
            await interaction.followup.send(f'Voice join failed: {exc}', ephemeral=True)

    async def handle_voice_leave(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await self.voice_runtime.disconnect(interaction.guild)
            await interaction.followup.send('Left the voice channel.', ephemeral=True)
        except Exception as exc:
            log.exception('Voice leave failed')
            await interaction.followup.send(f'Voice leave failed: {exc}', ephemeral=True)

    async def handle_speak(self, interaction: discord.Interaction, text: str) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await self.voice_runtime.connect_or_move(interaction)
            channel_name = await self.voice_runtime.speak_text(interaction.guild, text)
            await interaction.followup.send(
                f'Speaking now in **{channel_name}**.',
                embed=self.build_status_embed(interaction.guild.id if interaction.guild else None),
                files=self.brand_files(),
                ephemeral=True,
            )
        except Exception as exc:
            log.exception('Speak failed')
            await interaction.followup.send(f'Speak failed: {exc}', ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.bot.user is None:
            return

        is_dm = message.guild is None
        if is_dm:
            if not self.bot.settings.enable_mention_reply:
                return
            snapshot = self.state.get(None)
            prompt = message.content.strip()
        else:
            if self.bot.user not in message.mentions or message.mention_everyone:
                return
            snapshot = self.state.get(message.guild.id)
            if not snapshot.get('mention_enabled', True):
                return
            allowed = snapshot.get('allowed_channel_ids', [])
            if allowed and message.channel.id not in allowed:
                return
            prompt = message.content.replace(self.bot.user.mention, '').strip()

        if not prompt and not message.attachments:
            await message.reply('Mention me with a question, or attach a file/image/audio clip with instructions.')
            return

        attachment_context, image_urls = await self._extract_attachment_context(list(message.attachments))
        if not prompt:
            prompt = 'Analyze the attached content.'
        async with message.channel.typing():
            await self.animate_response(
                send_callback=lambda **kwargs: message.reply(**kwargs),
                edit_callback=lambda msg, **kwargs: msg.edit(**kwargs),
                prompt=prompt,
                mode=snapshot.get('mode', 'normal'),
                user_name=message.author.display_name,
                guild_name=message.guild.name if message.guild else None,
                system_note=snapshot.get('system_note', ''),
                attachment_context=attachment_context,
                image_urls=image_urls,
            )

    @app_commands.command(name='ask', description='Ask the AI with optional file or image context.')
    @app_commands.describe(prompt='Your question for the bot', mode='Optional temporary mode override for this request', attachment='Optional attachment')
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def ask(self, interaction: discord.Interaction, prompt: str, mode: app_commands.Choice[str] | None = None, attachment: discord.Attachment | None = None) -> None:
        attachment_context, image_urls = await self._extract_attachment_context([attachment] if attachment else [])
        await self.run_ai_flow(interaction, prompt, mode.value if mode else None, attachment_context=attachment_context, image_urls=image_urls)

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
        await self._send_setup_panel(interaction)

    @app_commands.command(name='panel', description='Open the command center panel again.')
    async def panel(self, interaction: discord.Interaction) -> None:
        await self._send_setup_panel(interaction)

    @app_commands.command(name='status', description='Inspect runtime state and asset health.')
    async def status(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=self.build_status_embed(interaction.guild.id if interaction.guild else None),
            files=self.brand_files(),
            ephemeral=True,
        )

    @app_commands.command(name='info', description='Show build info and links.')
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
        embed = help_embed(mode)
        apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)

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

    @app_commands.command(name='gallery', description='Show the UI asset gallery and icon catalog.')
    async def gallery(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id if interaction.guild else None
        await interaction.response.send_message(
            embed=self.build_gallery_embed(guild_id),
            files=self.brand_files(),
            ephemeral=True,
        )

    @app_commands.command(name='voice_join', description='Join your current voice channel.')
    async def voice_join(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_join(interaction)

    @app_commands.command(name='voice_leave', description='Leave the current voice channel.')
    async def voice_leave(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_leave(interaction)

    @app_commands.command(name='speak', description='Join your current voice channel and speak text with ElevenLabs.')
    @app_commands.describe(text='Text for the bot to speak in voice')
    async def speak(self, interaction: discord.Interaction, text: str) -> None:
        await self.handle_speak(interaction, text)




    @app_commands.command(name='transcribe', description='Transcribe an attached audio or video file with ElevenLabs.')
    @app_commands.describe(file='Audio or video attachment to transcribe')
    async def transcribe(self, interaction: discord.Interaction, file: discord.Attachment) -> None:
        await interaction.response.defer(thinking=True)
        try:
            attachment_context, _ = await self._extract_attachment_context([file])
            transcript = attachment_context.split('Transcription:\n', 1)[1] if 'Transcription:\n' in attachment_context else attachment_context
            mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
            embed = transcript_embed(mode, source_name=file.filename, transcript=transcript, language_code=None)
            apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
            await interaction.followup.send(embed=embed, files=self.brand_files())
        except Exception as exc:
            await interaction.followup.send(f'Transcription failed: {exc}', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MythicCog(bot))
