from __future__ import annotations

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
    music_embed,
    panel_embed,
    response_embed,
    status_embed,
    vision_embed,
)
from bot.ui.views import ControlCenterView, InfoLinksView

log = logging.getLogger(__name__)

TEXT_SUFFIXES = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.yml', '.yaml', '.html', '.css', '.sql', '.csv', '.log'}


class MythicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = bot.state_manager
        self.ai = bot.openrouter_client
        self.assets = bot.asset_manager
        self.presence_manager = bot.presence_manager
        self.voice_afk = bot.voice_afk_manager
        self.music = bot.music_service

    def brand_files(self) -> list[discord.File]:
        files: list[discord.File] = []
        banner = self.assets.banner_file()
        avatar = self.assets.avatar_file()
        if banner:
            files.append(banner)
        if avatar:
            files.append(avatar)
        return files

    def _is_creator(self, user_id: int | None) -> bool:
        return self.bot.settings.is_creator(user_id)

    def _voice_snapshot(self, guild: discord.Guild | None) -> dict[str, object]:
        return self.voice_afk.snapshot(guild)

    def _music_snapshot(self, guild: discord.Guild | None) -> dict[str, object]:
        return self.music.snapshot(guild)

    def build_status_embed(self, guild_id: int | None, state_override: dict | None = None, guild: discord.Guild | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = status_embed(
            snapshot,
            snapshot.get('mode', 'normal'),
            self.assets.asset_status(),
            self.bot.settings.openrouter_model,
            self._voice_snapshot(guild),
            self._music_snapshot(guild),
            bool(self.bot.settings.creator_ids),
        )
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_panel_embed(self, guild_id: int, state_override: dict | None = None, guild: discord.Guild | None = None) -> discord.Embed:
        snapshot = state_override or self.state.get(guild_id)
        embed = panel_embed(
            snapshot,
            snapshot.get('mode', 'normal'),
            self._voice_snapshot(guild),
            self._music_snapshot(guild),
            bool(self.bot.settings.creator_ids),
        )
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_info_embed(self, mode: str) -> discord.Embed:
        embed = info_embed(mode, self.bot.settings.openrouter_model, len(self.assets.icon_names()), bool(self.bot.settings.creator_ids))
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_gallery_embed(self, guild_id: int | None) -> discord.Embed:
        mode = self.state.get(guild_id).get('mode', 'normal')
        embed = gallery_embed(mode, self.assets.icon_names())
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_vision_embed(self, guild_id: int | None) -> discord.Embed:
        mode = self.state.get(guild_id).get('mode', 'normal')
        embed = vision_embed(mode)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    def build_music_embed(self, guild_id: int | None, guild: discord.Guild | None = None) -> discord.Embed:
        mode = self.state.get(guild_id).get('mode', 'normal')
        snap = self._music_snapshot(guild)
        details = (
            f"Now Playing: `{snap.get('current_title') or 'none'}`\n"
            f"Connected Voice: `{snap.get('channel_name') or 'none'}`\n"
            f"Queue Length: `{snap.get('queue_length', 0)}`\n"
            f"Loop: `{'ON' if snap.get('loop_enabled') else 'OFF'}`\n"
            'Use `/music` with a YouTube URL or raw video ID.'
        )
        embed = music_embed(mode, 'Music Queue', details)
        return apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)

    async def _send_setup_panel(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.send_message(
            embed=self.build_panel_embed(interaction.guild.id, guild=interaction.guild),
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
        is_creator: bool = False,
    ) -> None:
        preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
        files = self.brand_files()
        loading_message = await send_callback(
            embed=loading_embed(mode, random.choice(preset.loading_lines), prompt, user_name, is_creator=is_creator),
            files=files,
        )
        try:
            answer = await self.ai.chat(
                prompt=prompt,
                mode=mode,
                user_name=user_name,
                guild_name=guild_name,
                system_note=system_note,
                attachment_context=attachment_context,
                image_urls=image_urls or [],
                is_creator=is_creator,
            )
        except Exception as exc:
            log.exception('AI request failed')
            answer = f'AI request failed: {exc}'
        final_embed = response_embed(mode, prompt, answer, user_name, is_creator=is_creator)
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
        is_creator = self._is_creator(interaction.user.id)
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
            is_creator=is_creator,
        )

    async def _extract_attachment_context(self, attachments: list[discord.Attachment]) -> tuple[str, list[str]]:
        if not attachments:
            return '', []
        chunks: list[str] = []
        image_urls: list[str] = []
        for attachment in attachments[:5]:
            suffix = Path(attachment.filename).suffix.lower()
            content_type = (attachment.content_type or '').lower()
            meta = [
                f'Attachment: {attachment.filename}',
                f'Content type: {content_type or "unknown"}',
                f'Size bytes: {attachment.size}',
            ]
            if attachment.width:
                meta.append(f'Width: {attachment.width}')
            if attachment.height:
                meta.append(f'Height: {attachment.height}')
            if attachment.description:
                meta.append(f'Description: {attachment.description}')
            chunks.append('\n'.join(meta))
            if suffix in TEXT_SUFFIXES or content_type.startswith('text/'):
                try:
                    raw = await attachment.read()
                    text = raw.decode('utf-8', errors='ignore')
                except Exception as exc:
                    text = f'Failed to read text attachment: {exc}'
                if text:
                    chunks.append(text[:7000])
                continue
            if suffix == '.zip':
                try:
                    import io
                    raw = await attachment.read()
                    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                        names = '\n'.join(zf.namelist()[:120])
                    chunks.append('ZIP file entries:\n' + names)
                except Exception as exc:
                    chunks.append(f'Failed to inspect ZIP: {exc}')
                continue
            if content_type.startswith('image/'):
                image_urls.append(attachment.url)
                chunks.append(
                    'Image attachment detected. Inspect it carefully for visible text, scene details, UI structure, colors, warnings, charts, numbers, and anomalies.'
                )
                continue
            chunks.append('Unsupported attachment type for deep parsing in this build. Summarize its metadata only.')
        return '\n\n'.join(chunks)[:14000], image_urls

    async def handle_voice_afk(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            vc = await self.voice_afk.connect_or_move_afk(interaction)
            channel_name = getattr(vc.channel, 'name', 'voice') if getattr(vc, 'channel', None) else 'voice'
            await interaction.followup.send(
                f'AFK mode is active in **{channel_name}**. The bot will stay silent there until you move it or disconnect it.',
                embed=self.build_status_embed(interaction.guild.id if interaction.guild else None, guild=interaction.guild),
                files=self.brand_files(),
                ephemeral=True,
            )
        except Exception as exc:
            log.exception('Voice AFK join failed')
            await interaction.followup.send(f'Voice AFK join failed: {exc}', ephemeral=True)

    async def handle_voice_join(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            vc = await self.voice_afk.connect_or_move_live(interaction)
            channel_name = getattr(vc.channel, 'name', 'voice') if getattr(vc, 'channel', None) else 'voice'
            await interaction.followup.send(
                f'Joined **{channel_name}** for live playback commands.',
                embed=self.build_status_embed(interaction.guild.id if interaction.guild else None, guild=interaction.guild),
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
            await self.voice_afk.disconnect(interaction.guild)
            await interaction.followup.send('Left the voice channel.', ephemeral=True)
        except Exception as exc:
            log.exception('Voice leave failed')
            await interaction.followup.send(f'Voice leave failed: {exc}', ephemeral=True)

    async def handle_music_stop(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            await self.music.stop(interaction.guild)
            await interaction.followup.send('Stopped playback and cleared the queue.', ephemeral=True)
        except Exception as exc:
            log.exception('Music stop failed')
            await interaction.followup.send(f'Music stop failed: {exc}', ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.bot.user is None:
            return

        author_is_creator = self._is_creator(message.author.id)
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
            if not author_is_creator and not snapshot.get('mention_enabled', True):
                return
            allowed = snapshot.get('allowed_channel_ids', [])
            if not author_is_creator and allowed and message.channel.id not in allowed:
                return
            prompt = message.content.replace(self.bot.user.mention, '').strip()

        attachment_context, image_urls = await self._extract_attachment_context(list(message.attachments))
        if not prompt and image_urls:
            prompt = 'Analyze the attached image(s) in detail. Describe important objects, visible text, layout, colors, UI structure, and anything unusual.'
        elif not prompt and attachment_context:
            prompt = 'Analyze the attached content and summarize the most important details.'
        elif not prompt:
            await message.reply('Mention me with a question, or attach a file/image with instructions.')
            return

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
                is_creator=author_is_creator,
            )

    @app_commands.command(name='ask', description='Ask the AI with optional file or image context.')
    @app_commands.describe(prompt='Your question for the bot', mode='Optional temporary mode override for this request', attachment='Optional attachment')
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def ask(self, interaction: discord.Interaction, prompt: str, mode: app_commands.Choice[str] | None = None, attachment: discord.Attachment | None = None) -> None:
        attachment_context, image_urls = await self._extract_attachment_context([attachment] if attachment else [])
        await self.run_ai_flow(interaction, prompt, mode.value if mode else None, attachment_context=attachment_context, image_urls=image_urls)

    @app_commands.command(name='vision', description='Analyze one to three images in more detail.')
    @app_commands.describe(prompt='Optional instruction for the image analysis', image1='Primary image', image2='Optional extra image', image3='Optional extra image')
    async def vision(
        self,
        interaction: discord.Interaction,
        image1: discord.Attachment,
        prompt: str = '',
        image2: discord.Attachment | None = None,
        image3: discord.Attachment | None = None,
    ) -> None:
        attachments = [image1]
        if image2:
            attachments.append(image2)
        if image3:
            attachments.append(image3)
        attachment_context, image_urls = await self._extract_attachment_context(attachments)
        final_prompt = prompt.strip() or 'Analyze these image attachments in detail. Explain visible text, layout, objects, mood, style, and anything important.'
        await self.run_ai_flow(interaction, final_prompt, attachment_context=attachment_context, image_urls=image_urls)

    @app_commands.command(name='mode', description='Change the live server mode for everyone.')
    @app_commands.choices(mode=[app_commands.Choice(name=label, value=value) for label, value in MODE_CHOICES])
    async def mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        state = self.state.set_mode(interaction.guild.id, mode.value)
        self.presence_manager.set_mode(mode.value)
        await interaction.response.send_message(
            embed=self.build_status_embed(interaction.guild.id, state_override=state, guild=interaction.guild),
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
            embed=self.build_status_embed(interaction.guild.id if interaction.guild else None, guild=interaction.guild),
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
        embed = help_embed(mode, creator_configured=bool(self.bot.settings.creator_ids))
        apply_branding(embed, has_banner=self.assets.banner_path() is not None, has_avatar=self.assets.avatar_path() is not None)
        await interaction.response.send_message(embed=embed, files=self.brand_files(), ephemeral=True)

    @app_commands.command(name='creator', description='Show whether you are recognized as the creator.')
    async def creator(self, interaction: discord.Interaction) -> None:
        if self._is_creator(interaction.user.id):
            message = 'Creator verified. Supreme creator privileges are active for your Discord ID.'
        else:
            message = 'You are not configured as the creator in this build.'
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name='systemnote', description='Set or clear the server system note.')
    @app_commands.describe(note='Leave empty to clear the note')
    async def systemnote(self, interaction: discord.Interaction, note: str = '') -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        state = self.state.set_system_note(interaction.guild.id, note)
        await interaction.response.send_message(
            embed=self.build_status_embed(interaction.guild.id, state_override=state, guild=interaction.guild),
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

    @app_commands.command(name='vision_tips', description='Show image analysis tips and best prompt styles.')
    async def vision_tips(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild.id if interaction.guild else None
        await interaction.response.send_message(
            embed=self.build_vision_embed(guild_id),
            files=self.brand_files(),
            ephemeral=True,
        )

    @app_commands.command(name='voice_afk', description='Join your current voice channel in silent AFK mode.')
    async def voice_afk(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_afk(interaction)

    @app_commands.command(name='voice_join', description='Join your current voice channel for live playback commands.')
    async def voice_join(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_join(interaction)

    @app_commands.command(name='voice_leave', description='Leave the current voice channel.')
    async def voice_leave(self, interaction: discord.Interaction) -> None:
        await self.handle_voice_leave(interaction)

    @app_commands.command(name='music', description='Play direct YouTube audio from a URL or video ID.')
    @app_commands.describe(url='YouTube URL or raw 11-character video ID')
    async def music_command(self, interaction: discord.Interaction, url: str) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            track, position, started = await self.music.enqueue(interaction, url)
            status_line = 'Playback started.' if started else f'Queued at position {position}.'
            details = (
                f"Title: **{track.title}**\n"
                f"URL: {track.webpage_url}\n"
                f"Requested by: {interaction.user.display_name}\n\n"
                f"{status_line}"
            )
            await interaction.followup.send(
                embed=apply_branding(
                    music_embed(self.state.get(interaction.guild.id).get('mode', 'normal'), 'YouTube Playback', details),
                    has_banner=self.assets.banner_path() is not None,
                    has_avatar=self.assets.avatar_path() is not None,
                ),
                files=self.brand_files(),
                ephemeral=True,
            )
        except Exception as exc:
            log.exception('Music failed')
            hint = ''
            if "Sign in to confirm you're not a bot" in str(exc) or 'cookies' in str(exc).lower():
                hint = '\nTip: set YTDLP_COOKIES_B64 and YTDLP_USER_AGENT in Railway if YouTube blocks extraction.'
            await interaction.followup.send(f'Music failed: {exc}{hint}', ephemeral=True)

    @app_commands.command(name='music_skip', description='Skip the current track.')
    async def music_skip(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            title = await self.music.skip(interaction.guild)
            await interaction.followup.send(f'Skipped: **{title}**', ephemeral=True)
        except Exception as exc:
            log.exception('Music skip failed')
            await interaction.followup.send(f'Music skip failed: {exc}', ephemeral=True)

    @app_commands.command(name='music_stop', description='Stop playback and clear the queue.')
    async def music_stop(self, interaction: discord.Interaction) -> None:
        await self.handle_music_stop(interaction)

    @app_commands.command(name='music_loop', description='Toggle loop mode for the current queue.')
    async def music_loop(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message('This command works only inside a server.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            enabled = await self.music.toggle_loop(interaction.guild)
            await interaction.followup.send(f'Loop is now **{"ON" if enabled else "OFF"}**.', ephemeral=True)
        except Exception as exc:
            log.exception('Music loop failed')
            await interaction.followup.send(f'Music loop failed: {exc}', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MythicCog(bot))
