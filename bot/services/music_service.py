from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord
import yt_dlp

from bot.services.ffmpeg_utils import resolve_ffmpeg_executable

if TYPE_CHECKING:
    from bot.state import GuildStateManager

log = logging.getLogger(__name__)


@dataclass(slots=True)
class MusicSession:
    title: str = ''
    webpage_url: str = ''
    stream_url: str = ''
    loop: bool = False
    lock: asyncio.Lock | None = None

    def __post_init__(self) -> None:
        if self.lock is None:
            self.lock = asyncio.Lock()


class MusicManager:
    def __init__(self, state_manager: 'GuildStateManager', bot: discord.Client) -> None:
        self.state_manager = state_manager
        self.bot = bot
        self._sessions: dict[int, MusicSession] = {}

    def _session(self, guild_id: int) -> MusicSession:
        session = self._sessions.get(guild_id)
        if session is None:
            session = MusicSession()
            self._sessions[guild_id] = session
        return session

    @staticmethod
    def validate_youtube(url: str) -> bool:
        lowered = url.lower()
        return 'youtube.com/' in lowered or 'youtu.be/' in lowered

    @staticmethod
    def extract(url: str) -> tuple[str, str]:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        stream_url = info.get('url')
        title = info.get('title') or 'YouTube audio'
        if not stream_url:
            raise RuntimeError('Failed to extract a playable YouTube stream.')
        return title, stream_url

    async def play_youtube(self, guild: discord.Guild, voice_channel: discord.VoiceChannel, url: str) -> str:
        if not self.validate_youtube(url):
            raise RuntimeError('Only YouTube links are supported in this build.')
        session = self._session(guild.id)
        async with session.lock:
            title, stream_url = await asyncio.to_thread(self.extract, url)
            vc = guild.voice_client
            if vc is None:
                vc = await voice_channel.connect()
            elif vc.channel.id != voice_channel.id:
                await vc.move_to(voice_channel)
            if vc.is_playing() or vc.is_paused():
                vc.stop()
                await asyncio.sleep(0.25)

            session.title = title
            session.stream_url = stream_url
            session.webpage_url = url

            def play_current() -> None:
                ffmpeg = resolve_ffmpeg_executable()
                source = discord.FFmpegPCMAudio(
                    session.stream_url,
                    executable=ffmpeg,
                    before_options='-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn',
                )

                def after_play(exc: Exception | None) -> None:
                    if exc:
                        log.warning('Music playback ended with error: %s', exc)
                    if session.loop and session.webpage_url:
                        self.bot.loop.call_soon_threadsafe(lambda: self.bot.loop.create_task(self._replay(guild.id)))
                    else:
                        session.title = ''
                        session.stream_url = ''
                        session.webpage_url = ''

                vc.play(source, after=after_play)

            play_current()
            return title

    async def _replay(self, guild_id: int) -> None:
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return
        session = self._sessions.get(guild_id)
        if session is None or not session.webpage_url:
            return
        vc = guild.voice_client
        if vc is None:
            return
        await asyncio.sleep(0.5)
        ffmpeg = resolve_ffmpeg_executable()
        source = discord.FFmpegPCMAudio(
            session.stream_url,
            executable=ffmpeg,
            before_options='-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn',
        )

        def after_play(exc: Exception | None) -> None:
            if exc:
                log.warning('Music loop ended with error: %s', exc)
            if session.loop and session.webpage_url:
                self.bot.loop.call_soon_threadsafe(lambda: self.bot.loop.create_task(self._replay(guild_id)))
            else:
                session.title = ''
                session.stream_url = ''
                session.webpage_url = ''

        vc.play(source, after=after_play)

    async def stop(self, guild: discord.Guild | None) -> None:
        if guild is None:
            return
        vc = guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
        self._sessions.pop(guild.id, None)

    async def disconnect(self, guild: discord.Guild | None) -> None:
        if guild is None:
            return
        await self.stop(guild)
        vc = guild.voice_client
        if vc:
            await vc.disconnect(force=True)

    def set_loop(self, guild_id: int, enabled: bool) -> bool:
        session = self._session(guild_id)
        session.loop = bool(enabled)
        self.state_manager.set_music_loop(guild_id, enabled)
        return bool(enabled)

    def is_playing(self, guild_id: int | None) -> bool:
        if guild_id is None:
            return False
        session = self._sessions.get(guild_id)
        return bool(session and session.title)

    def snapshot(self, guild_id: int | None) -> dict:
        if guild_id is None:
            return {'title': '', 'url': '', 'loop': False, 'active': False}
        session = self._sessions.get(guild_id)
        if session is None:
            state = self.state_manager.get(guild_id)
            return {'title': '', 'url': '', 'loop': bool(state.get('music_loop')), 'active': False}
        return {
            'title': session.title,
            'url': session.webpage_url,
            'loop': session.loop,
            'active': bool(session.title),
        }
