from __future__ import annotations

import asyncio
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import discord
import yt_dlp

from bot.services.ffmpeg_utils import resolve_ffmpeg_executable

log = logging.getLogger(__name__)


@dataclass(slots=True)
class MusicTrack:
    title: str
    webpage_url: str
    stream_url: str
    platform: str
    duration: int | None = None
    thumbnail: str | None = None


@dataclass(slots=True)
class MusicSession:
    queue: list[MusicTrack] = field(default_factory=list)
    loop_enabled: bool = False
    current: MusicTrack | None = None
    text_channel_id: int | None = None


class MusicService:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.sessions: dict[int, MusicSession] = {}

    def _session(self, guild_id: int) -> MusicSession:
        return self.sessions.setdefault(guild_id, MusicSession())

    @staticmethod
    def _base_ytdlp_options() -> dict:
        return {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extract_flat': False,
        }

    def _extract_info(self, query: str, *, search: bool = False) -> dict:
        opts = self._base_ytdlp_options()
        if search and not query.startswith(('http://', 'https://')):
            query = f'ytsearch1:{query}'
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
        if info is None:
            raise RuntimeError('No media info found for the provided query.')
        if 'entries' in info and info['entries']:
            info = info['entries'][0]
        if not info:
            raise RuntimeError('No playable result found.')
        return info

    def resolve_track(self, url: str, platform: str) -> MusicTrack:
        platform = (platform or 'auto').lower()
        info = None
        if platform == 'spotify' or 'spotify.com' in url:
            meta = self._extract_info(url)
            artist = ''
            artists = meta.get('artists') or []
            if artists:
                artist = artists[0]
            elif meta.get('artist'):
                artist = meta['artist']
            search_query = ' '.join(part for part in [meta.get('track') or meta.get('title') or '', artist, 'audio'] if part).strip()
            if not search_query:
                raise RuntimeError('Could not derive a search query from the Spotify URL.')
            info = self._extract_info(search_query, search=True)
            platform = 'spotify->youtube'
        else:
            info = self._extract_info(url)
            if platform == 'auto':
                domain = (info.get('webpage_url_domain') or '')
                platform = domain or 'auto'
        stream_url = info.get('url')
        if not stream_url:
            raise RuntimeError('Failed to resolve a direct audio stream URL.')
        return MusicTrack(
            title=info.get('title') or 'Unknown title',
            webpage_url=info.get('webpage_url') or url,
            stream_url=stream_url,
            platform=platform,
            duration=info.get('duration'),
            thumbnail=info.get('thumbnail'),
        )

    async def enqueue(self, guild: discord.Guild, voice_client: discord.VoiceClient, *, url: str, platform: str, text_channel_id: int | None = None) -> MusicTrack:
        session = self._session(guild.id)
        track = await asyncio.to_thread(self.resolve_track, url, platform)
        session.queue.append(track)
        if text_channel_id is not None:
            session.text_channel_id = text_channel_id
        if not voice_client.is_playing() and session.current is None:
            await self._play_next(guild, voice_client)
        return track

    async def _play_next(self, guild: discord.Guild, voice_client: discord.VoiceClient) -> None:
        session = self._session(guild.id)
        if not session.queue:
            session.current = None
            return
        track = session.queue[0] if session.loop_enabled and session.current is not None else session.queue.pop(0)
        session.current = track
        ffmpeg_executable = resolve_ffmpeg_executable()
        source = discord.FFmpegPCMAudio(
            track.stream_url,
            executable=ffmpeg_executable,
            before_options='-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-vn -loglevel error',
            stderr=subprocess.DEVNULL,
        )

        def _after(exc: Exception | None) -> None:
            async def _continue() -> None:
                if exc:
                    log.error('Music playback error: %s', exc)
                if session.loop_enabled and track not in session.queue:
                    session.queue.insert(0, track)
                await self._play_next(guild, voice_client)
            self.bot.loop.call_soon_threadsafe(lambda: asyncio.create_task(_continue()))

        voice_client.play(source, after=_after)
        if session.text_channel_id:
            channel = self.bot.get_channel(session.text_channel_id)
            if channel and hasattr(channel, 'send'):
                try:
                    self.bot.loop.create_task(channel.send(f'🎵 Now playing: **{track.title}**'))
                except Exception:
                    pass

    async def stop(self, guild: discord.Guild | None) -> str:
        if guild is None:
            raise RuntimeError('Music stop works only inside a server.')
        session = self._session(guild.id)
        session.queue.clear()
        session.current = None
        vc = guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
        return 'Music stopped and queue cleared.'

    def toggle_loop(self, guild_id: int) -> bool:
        session = self._session(guild_id)
        session.loop_enabled = not session.loop_enabled
        return session.loop_enabled

    def snapshot(self, guild_id: int) -> dict:
        session = self._session(guild_id)
        return {
            'loop_enabled': session.loop_enabled,
            'current_title': session.current.title if session.current else None,
            'queue_size': len(session.queue),
            'platform': session.current.platform if session.current else None,
            'thumbnail': session.current.thumbnail if session.current else None,
        }
