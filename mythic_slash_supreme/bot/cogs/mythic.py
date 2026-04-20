from __future__ import annotations

import asyncio
import logging
import random
import zipfile
from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from bot.constants import MODE_CHOICES, MODE_PRESETS
from bot.ui.embeds import (
    apply_branding,
    help_embed,
    info_embed,
    loading_embed,
    panel_embed,
    profile_embed,
    response_embed,
    scene_embed,
    status_embed,
    transcript_embed,
    voice_architecture_embed,
    voice_hub_embed,
)
from bot.ui.views import ControlCenterView, InfoLinksView, VoiceHubView

log = logging.getLogger(__name__)

TEXT_SUFFIXES = {
    '.txt', '.md', '.py', '.js', '.ts', '.json', '.yml', '.yaml', '.html',
    '.css', '.xml', '.csv', '.log', '.ini', '.toml', '.sh', '.sql',
}
AUDIO_SUFFIXES = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.mp4', '.webm', '.mov'}


class MythicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = bot.state_manager
        self.ai = bot.openrouter_client
        self.assets = bot.asset_manager
        self.presence_manager = bot.presence_manager
        self.stt = bot.assemblyai_client
        self.tts = bot.tts_service
        self.voice_runtime = bot.voice_runtime
        self.music_service = bot.music_service
        self.analyzer = AttachmentAnalyzer(self.stt)

    def brand_files(self) -> list[discord.File]:
        files: list[discord.File] = []
        banner = self.assets.banner_file()
        avatar = self.assets.avatar_file()
        if banner:
            files.append(banner)
        if avatar:
            files.append(avatar)
        return files

    def voice_hub_view(self, guild_id: int) -> VoiceHubView:
        return VoiceHubView(self, guild_id)

    def build_status_embed(self, guild_id: int | None, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = status_embed(snapshot, snapshot.get('mode', 'normal'), self.assets.asset_status(), self.bot.settings.openrouter_model)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_panel_embed(self, guild_id: int | None, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        activation_phrase = snapshot.get('voice_wake_phrase') or self.bot.settings.activation_phrase
        embed = panel_embed(snapshot, snapshot.get('mode', 'normal'), activation_phrase)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_info_embed(self, mode: str) -> discord.Embed:
        embed = info_embed(mode, self.bot.settings.openrouter_model, len(self.assets.icon_names()))
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_voice_hub_embed(self, guild_id: int | None, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        mode = snapshot.get('mode', 'normal')
        runtime = self.voice_runtime.snapshot(self.bot.get_guild(guild_id) if guild_id else None, snapshot)
        text_probe = 'مرحبا' if snapshot.get('voice_output_language', 'auto') in {'auto', 'ar'} else 'hello'
        preferred = snapshot.get('voice_output_language', 'auto')
        if preferred not in {'ar', 'en'}:
            preferred = None
        sample_voice = self.tts.pick_voice(text_probe, preferred=preferred)
        embed = voice_hub_embed(
            mode,
            connected_channel=runtime.connected_channel,
            stt_enabled=self.stt.enabled,
            tts_voice=sample_voice,
            activation_phrase=snapshot.get('voice_wake_phrase') or self.bot.settings.activation_phrase,
            armed=snapshot.get('voice_armed', False),
            receive_supported=runtime.receive_supported,
            receive_active=runtime.receive_active,
            input_language=snapshot.get('voice_input_language', 'auto'),
            output_language=snapshot.get('voice_output_language', 'auto'),
            silence_seconds=float(snapshot.get('voice_silence_seconds', self.bot.settings.voice_silence_seconds)),
        )
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_voice_architecture_embed(self, guild_id: int | None, state_override: dict | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        mode = snapshot.get('mode', 'normal')
        runtime = self.voice_runtime.snapshot(self.bot.get_guild(guild_id) if guild_id else None, snapshot)
        embed = voice_architecture_embed(mode, snapshot, runtime.note, runtime.receive_supported)
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


    def build_music_embed(self, snapshot: dict[str, Any], *, title: str = 'Music Hub', url: str | None = None, track_title: str | None = None) -> discord.Embed:
        embed = discord.Embed(title='🎵 ' + title, color=0x8b5cf6)
        embed.description = 'Stream audio from supported platforms with a branded queue card.'
        embed.add_field(name='Now Playing', value=track_title or snapshot.get('current_title') or 'Nothing right now', inline=False)
        embed.add_field(name='Loop', value='ON' if snapshot.get('loop_enabled') else 'OFF', inline=True)
        embed.add_field(name='Queue', value=str(snapshot.get('queue_size', 0)), inline=True)
        embed.add_field(name='Platform', value=str(snapshot.get('platform') or 'n/a'), inline=True)
        if url:
            embed.add_field(name='Source', value=url[:1024], inline=False)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

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
        image_inputs: list[str] | None = None,
    ) -> None:
        preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
        files = self.brand_files()
        loading_message = await send_callback(embed=loading_embed(mode, preset.loading_lines[0], prompt, user_name), files=files)
        task = asyncio.create_task(
            self.ai.chat(
                prompt=prompt,
                mode=mode,
                user_name=user_name,
                guild_name=guild_name,
                system_note=system_note,
                attachment_context=attachment_context,
                image_inputs=image_inputs,
            )
        )
        tick = 1
        while not task.done():
            await asyncio.sleep(1.0)
            line = preset.loading_lines[tick % len(preset.loading_lines)]
            tick += 1
            try:
                await edit_callback(
                    loading_message,
                    embed=loading_embed(mode, line, prompt, user_name),
                    attachments=self.brand_files(),
                )
            except discord.HTTPException:
                pass
            if tick > 10 and not task.done():
                break
        try:
            answer = await task
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
        image_inputs: list[str] | None = None,
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
            image_inputs=image_inputs,
        )

    async def _extract_attachment_context(self, attachments: list[discord.Attachment]) -> tuple[str, list[str]]:
        return await self.analyzer.analyze(attachments)

    async def _ensure_voice_connection(self, interaction: discord.Interaction) -> discord.VoiceClient:
        return await self.voice_runtime.connect_or_move(interaction)

    async def _play_tts(self, interaction: discord.Interaction, text: str) -> str:
        guild = interaction.guild
        if guild is None:
            raise RuntimeError('Voice speak works only inside a server.')
        await self._ensure_voice_connection(interaction)
        snapshot = self.state.get(guild.id)
        preferred = snapshot.get('voice_output_language', 'auto')
        if preferred not in {'ar', 'en'}:
            preferred = None
        return await self.voice_runtime.speak_text(guild, text, preferred_language=preferred)

    async def handle_voice_action(self, interaction: discord.Interaction, *, action: str, text: str | None) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        guild_id = interaction.guild.id if interaction.guild else None
        try:
            if action == 'join':
                vc = await self._ensure_voice_connection(interaction)
                embed = self.build_voice_hub_embed(guild_id)
                await interaction.followup.send(
                    f'Joined **{vc.channel.name}**.',
                    embed=embed,
                    files=self.brand_files(),
                    ephemeral=True,
                    view=self.voice_hub_view(interaction.guild.id),
                )
                return
            if action == 'leave':
                await self.voice_runtime.disconnect(interaction.guild)
                state = self.state.set_voice_armed(interaction.guild.id, False) if interaction.guild else self.state.get(None)
                await interaction.followup.send(
                    'Disconnected from voice.',
                    embed=self.build_voice_hub_embed(guild_id, state_override=state),
                    files=self.brand_files(),
                    ephemeral=True,
                    view=self.voice_hub_view(interaction.guild.id) if interaction.guild else None,
                )
                return
            if action == 'speak':
                if not text:
                    raise RuntimeError('Provide text to speak.')
                channel_name = await self._play_tts(interaction, text)
                await interaction.followup.send(
                    f'Speaking now in **{channel_name}**.',
                    embed=self.build_voice_hub_embed(guild_id),
                    files=self.brand_files(),
                    ephemeral=True,
                    view=self.voice_hub_view(interaction.guild.id),
                )
                return
            raise RuntimeError('Unknown voice action.')
        except Exception as exc:
            await interaction.followup.send(f'Voice action failed: {exc}', ephemeral=True)

    async def handle_voice_arm(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            note = await self.voice_runtime.arm(interaction.guild, text_channel_id=interaction.channel_id)
            state = self.state.set_voice_armed(interaction.guild.id, True)
            await interaction.followup.send(
                note,
                embed=self.build_voice_hub_embed(interaction.guild.id, state_override=state),
                files=self.brand_files(),
                ephemeral=True,
                view=self.voice_hub_view(interaction.guild.id),
            )
        except Exception as exc:
            await interaction.followup.send(f'Voice arm failed: {exc}', ephemeral=True)

    async def handle_voice_disarm(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            note = await self.voice_runtime.disarm(interaction.guild)
            state = self.state.set_voice_armed(interaction.guild.id, False)
            await interaction.followup.send(
                note,
                embed=self.build_voice_hub_embed(interaction.guild.id, state_override=state),
                files=self.brand_files(),
                ephemeral=True,
                view=self.voice_hub_view(interaction.guild.id),
            )
        except Exception as exc:
            await interaction.followup.send(f'Voice disarm failed: {exc}', ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.bot.user is None:
            return

        is_dm = message.guild is None
        if is_dm:
            if not self.bot.settings.enable_dm_ai:
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
            if is_dm:
                await message.reply('Send a question, or attach a file/audio clip with a request.')
                return
            await message.reply(
                f'ابدأ رسالتك بـ **{snapshot.get("voice_wake_phrase", self.bot.settings.activation_phrase)}** ثم اطلب ما تريد، أو استخدم `/setup`.',
                embed=self.build_panel_embed(message.guild.id),
                view=ControlCenterView(self, message.guild.id),
                files=self.brand_files(),
            )
            return

        lowered = prompt.lower()
        if not is_dm:
            phrase = (snapshot.get('voice_wake_phrase') or self.bot.settings.activation_phrase).lower()
            if lowered.startswith(phrase):
                prompt = prompt[len(phrase):].strip(' :,-')
            elif message.attachments:
                prompt = prompt or 'حلل هذا المرفق'
            else:
                return

        attachment_context, image_inputs = await self._extract_attachment_context(list(message.attachments))
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
                image_inputs=image_inputs,
            )

    @app_commands.command(name='ask', description='Ask the AI with optional file context.')
    @app_commands.describe(prompt='Your question for the bot', mode='Optional temporary mode override for this request', attachment='Optional text, audio, video, or zip attachment')
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def ask(self, interaction: discord.Interaction, prompt: str, mode: app_commands.Choice[str] | None = None, attachment: discord.Attachment | None = None) -> None:
        attachment_context, image_inputs = await self._extract_attachment_context([attachment] if attachment else [])
        await self.run_ai_flow(interaction, prompt, mode.value if mode else None, attachment_context=attachment_context, image_inputs=image_inputs)

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


    @app_commands.command(name='music', description='Play music from YouTube, Spotify, or a direct audio page.')
    @app_commands.describe(url='Track or playlist URL', platform='Choose the link platform for better routing')
    @app_commands.choices(platform=[
        app_commands.Choice(name='Auto', value='auto'),
        app_commands.Choice(name='YouTube', value='youtube'),
        app_commands.Choice(name='Spotify', value='spotify'),
        app_commands.Choice(name='Other', value='other'),
    ])
    async def music(self, interaction: discord.Interaction, url: str, platform: app_commands.Choice[str]) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            vc = await self._ensure_voice_connection(interaction)
            track = await self.music_service.enqueue(interaction.guild, vc, url=url, platform=platform.value, text_channel_id=interaction.channel_id)
            snap = self.music_service.snapshot(interaction.guild.id)
            embed = self.build_music_embed(snap, title='Music queued', url=track.webpage_url, track_title=track.title)
            await interaction.followup.send(embed=embed, files=self.brand_files(), ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f'Music command failed: {exc}', ephemeral=True)

    @app_commands.command(name='end_music', description='Stop music and clear the queue.')
    async def end_music(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        try:
            note = await self.music_service.stop(interaction.guild)
            embed = self.build_music_embed(self.music_service.snapshot(interaction.guild.id), title='Music stopped')
            await interaction.followup.send(note, embed=embed, files=self.brand_files(), ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f'End music failed: {exc}', ephemeral=True)

    @app_commands.command(name='loop', description='Toggle music looping for the current guild.')
    async def loop(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        enabled = self.music_service.toggle_loop(interaction.guild.id)
        embed = self.build_music_embed(self.music_service.snapshot(interaction.guild.id), title='Loop updated')
        await interaction.response.send_message(f'Loop is now **{'ON' if enabled else 'OFF'}**.', embed=embed, files=self.brand_files(), ephemeral=True)

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

    @app_commands.command(name='profile', description='Show branding assets and icon preview.')
    async def profile(self, interaction: discord.Interaction) -> None:
        mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        embed = profile_embed(mode, self.assets.asset_status(), self.assets.icon_names())
        apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='scene', description="Preview a mode's animated text lines.")
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def scene(self, interaction: discord.Interaction, mode: app_commands.Choice[str] | None = None) -> None:
        mode_key = mode.value if mode else self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
        preset = MODE_PRESETS.get(mode_key, MODE_PRESETS['normal'])
        sample_loading = random.sample(preset.loading_lines, k=min(8, len(preset.loading_lines)))
        sample_presence = random.sample(preset.presence_lines, k=min(8, len(preset.presence_lines)))
        embed = scene_embed(mode_key, sample_loading, sample_presence)
        apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='voice_action', description='Join voice, leave voice, or speak text in voice.')
    @app_commands.describe(action='Voice action to perform', text='Text to speak when using the speak action')
    @app_commands.choices(action=[
        app_commands.Choice(name='join', value='join'),
        app_commands.Choice(name='leave', value='leave'),
        app_commands.Choice(name='speak', value='speak'),
    ])
    async def voice_action(self, interaction: discord.Interaction, action: app_commands.Choice[str], text: str | None = None) -> None:
        await self.handle_voice_action(interaction, action=action.value, text=text)

    @app_commands.command(name='voice_arm', description='Arm the official bot voice runtime after joining voice.')
    async def voice_arm(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_arm(interaction)

    @app_commands.command(name='voice_disarm', description='Disarm the official bot voice runtime.')
    async def voice_disarm(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_disarm(interaction)

    @app_commands.command(name='voice_status', description='Inspect the official voice runtime and wake profile.')
    async def voice_status(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id if interaction.guild else None
        await interaction.response.send_message(
            embed=self.build_voice_hub_embed(guild_id),
            files=self.brand_files(),
            ephemeral=True,
            view=self.voice_hub_view(interaction.guild.id) if interaction.guild else None,
        )

    @app_commands.command(name='voice_design', description='Show the official bot voice architecture card.')
    async def voice_design(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id if interaction.guild else None
        await interaction.response.send_message(
            embed=self.build_voice_architecture_embed(guild_id),
            files=self.brand_files(),
            ephemeral=True,
        )


    @app_commands.command(name='speak', description='Speak text in the current voice channel.')
    @app_commands.describe(text='Text for the bot to speak in voice')
    async def speak(self, interaction: discord.Interaction, text: str) -> None:
        await self.handle_voice_action(interaction, action='speak', text=text)

    @app_commands.command(name='voice_join', description='Join your current voice channel.')
    async def voice_join(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_action(interaction, action='join', text=None)

    @app_commands.command(name='voice_leave', description='Leave the current voice channel.')
    async def voice_leave(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_action(interaction, action='leave', text=None)

    @app_commands.command(name='transcribe', description='Transcribe an attached audio or video file with AssemblyAI.')
    @app_commands.describe(file='Audio or video attachment to transcribe')
    async def transcribe(self, interaction: discord.Interaction, file: discord.Attachment) -> None:
        await interaction.response.defer(thinking=True)
        try:
            context = await self._extract_attachment_context([file])
            if 'Transcription:' in context:
                transcript = context.split('Transcription:\n', 1)[1]
            else:
                transcript = context
            mode = self.state.get(interaction.guild.id if interaction.guild else None).get('mode', 'normal')
            embed = transcript_embed(mode, source_name=file.filename, transcript=transcript, language_code=None)
            apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
            await interaction.followup.send(embed=embed, files=self.brand_files())
        except Exception as exc:
            await interaction.followup.send(f'Transcription failed: {exc}', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MythicCog(bot))
