from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque

import discord
import yt_dlp

log = logging.getLogger(__name__)


@dataclass(slots=True)
class Track:
    title: str
    webpage_url: str
    stream_url: str
    duration: int | None
    requested_by: str


@dataclass(slots=True)
class GuildMusicState:
    queue: Deque[Track] = field(default_factory=deque)
    current: Track | None = None
    loop_enabled: bool = False


class MusicService:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.states: dict[int, GuildMusicState] = {}
        self._cookie_file_path: str | None = None

    def state_for(self, guild_id: int) -> GuildMusicState:
        return self.states.setdefault(guild_id, GuildMusicState())

    def snapshot(self, guild: discord.Guild | None) -> dict[str, object]:
        if guild is None:
            return {
                "connected": False,
                "channel_name": None,
                "current_title": None,
                "queue_length": 0,
                "loop_enabled": False,
            }
        state = self.state_for(guild.id)
        vc = guild.voice_client
        return {
            "connected": bool(vc and vc.channel),
            "channel_name": getattr(vc.channel, "name", None) if vc and vc.channel else None,
            "current_title": state.current.title if state.current else None,
            "queue_length": len(state.queue),
            "loop_enabled": state.loop_enabled,
        }


    def _resolve_cookie_file(self) -> str | None:
        cookie_file = os.getenv("YTDLP_COOKIE_FILE", "").strip()
        if cookie_file and Path(cookie_file).exists():
            return cookie_file

        b64_file = os.getenv("YTDLP_COOKIES_B64_FILE", "").strip()
        b64 = os.getenv("YTDLP_COOKIES_B64", "").strip()
        raw = os.getenv("YTDLP_COOKIES", "")
        content = ""

        if b64_file:
            try:
                file_path = Path(b64_file)
                if file_path.exists():
                    b64 = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                else:
                    log.warning("YTDLP_COOKIES_B64_FILE does not exist: %s", b64_file)
            except Exception:
                log.exception("Failed to read YTDLP_COOKIES_B64_FILE")

        if b64:
            try:
                content = base64.b64decode(b64).decode("utf-8", errors="ignore")
            except Exception:
                log.exception("Failed to decode YTDLP_COOKIES_B64")
        elif raw.strip():
            content = raw

        if not content.strip():
            return None

        if self._cookie_file_path and Path(self._cookie_file_path).exists():
            return self._cookie_file_path

        fd, path = tempfile.mkstemp(prefix="ytcookies_", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        self._cookie_file_path = path
        return path

    def _ydl_opts(self) -> dict:
        headers: dict[str, str] = {}
        user_agent = os.getenv("YTDLP_USER_AGENT", "").strip()
        if user_agent:
            headers["User-Agent"] = user_agent

        opts: dict[str, object] = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "default_search": "auto",
            "skip_download": True,
            "socket_timeout": 30,
            "youtube_include_dash_manifest": True,
            "youtube_include_hls_manifest": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web", "ios", "tv"],
                }
            },
        }

        cookie_file = self._resolve_cookie_file()
        if cookie_file:
            opts["cookiefile"] = cookie_file
        if headers:
            opts["http_headers"] = headers

        return opts

    def _normalize_query(self, query: str) -> str:
        cleaned = query.strip()
        if len(cleaned) == 11 and all(c.isalnum() or c in "-_" for c in cleaned):
            return f"https://www.youtube.com/watch?v={cleaned}"
        return cleaned

    def _score_format(self, fmt: dict) -> tuple:
        ext = (fmt.get("ext") or "").lower()
        abr = fmt.get("abr") or 0
        tbr = fmt.get("tbr") or 0
        acodec = (fmt.get("acodec") or "none").lower()
        vcodec = (fmt.get("vcodec") or "none").lower()
        protocol = (fmt.get("protocol") or "").lower()

        has_audio = 1 if acodec != "none" else 0
        audio_only = 1 if has_audio and vcodec == "none" else 0
        progressive = 1 if has_audio and vcodec != "none" else 0
        ext_pref = 3 if ext == "m4a" else 2 if ext == "webm" else 1 if ext in {"mp4", "m3u8"} else 0
        proto_pref = 2 if protocol.startswith(("https", "http")) else 1 if "m3u8" in protocol else 0

        return (has_audio, audio_only, progressive, ext_pref, proto_pref, abr, tbr)

    def _pick_best_audio_url(self, info: dict) -> str:
        requested_formats = info.get("requested_formats") or []
        requested_urls = [
            f for f in requested_formats
            if f.get("url") and (f.get("acodec") or "none") != "none"
        ]
        if requested_urls:
            best_requested = sorted(requested_urls, key=self._score_format, reverse=True)[0]
            return best_requested["url"]

        formats = info.get("formats") or []
        usable: list[dict] = []
        for fmt in formats:
            url = fmt.get("url") or ""
            ext = (fmt.get("ext") or "").lower()
            fid = str(fmt.get("format_id") or "").lower()
            note = str(fmt.get("format_note") or "").lower()
            acodec = (fmt.get("acodec") or "none").lower()

            if not url:
                continue
            if "/storyboard" in url or "storyboard" in note or fid.startswith("sb"):
                continue
            if ext in {"jpg", "jpeg", "png", "webp", "mhtml"}:
                continue
            if acodec == "none":
                continue

            usable.append(fmt)

        if not usable:
            raise RuntimeError(
                "No playable audio format was found for this video. "
                "This usually means YouTube blocked the server-side extractor for this item."
            )

        best = sorted(usable, key=self._score_format, reverse=True)[0]
        return best["url"]

    def _extract_track_sync(self, query: str) -> Track:
        normalized = self._normalize_query(query)

        with yt_dlp.YoutubeDL(self._ydl_opts()) as ydl:
            try:
                info = ydl.extract_info(normalized, download=False, process=False)
            except Exception as exc:
                raise RuntimeError(f"yt-dlp could not inspect this YouTube URL: {exc}") from exc

            if info is None:
                raise RuntimeError("No media info was returned by yt-dlp.")

            if "entries" in info:
                entries = [entry for entry in info.get("entries") or [] if entry]
                if not entries:
                    raise RuntimeError("Playlist or search returned no playable entries.")
                info = entries[0]
                if info.get("url") and not info.get("formats") and not info.get("requested_formats"):
                    info = ydl.extract_info(info["url"], download=False, process=False)

        if info is None:
            raise RuntimeError("No media info was returned by yt-dlp.")

        stream_url = info.get("url")
        if not stream_url or (info.get("acodec") or "none") == "none":
            stream_url = self._pick_best_audio_url(info)

        return Track(
            title=info.get("title") or "Unknown title",
            webpage_url=info.get("webpage_url") or normalized,
            stream_url=stream_url,
            duration=info.get("duration"),
            requested_by="unknown",
        )

    async def connect_to_author(self, interaction: discord.Interaction) -> discord.VoiceClient:
        if interaction.guild is None:
            raise RuntimeError("Music works only inside a server.")

        author_voice = getattr(interaction.user, "voice", None)
        if author_voice is None or author_voice.channel is None:
            raise RuntimeError("Join a voice channel first.")

        target = author_voice.channel
        existing = interaction.guild.voice_client

        if existing and existing.channel and existing.channel.id != target.id:
            await existing.move_to(target)
            try:
                await interaction.guild.change_voice_state(
                    channel=target,
                    self_mute=False,
                    self_deaf=False,
                )
            except Exception:
                log.debug("Could not clear self-mute/deafen for music playback.", exc_info=True)
            return existing

        if existing and existing.channel and existing.channel.id == target.id:
            return existing

        vc = await target.connect()
        try:
            await interaction.guild.change_voice_state(
                channel=target,
                self_mute=False,
                self_deaf=False,
            )
        except Exception:
            log.debug("Could not clear self-mute/deafen after music connect.", exc_info=True)
        return vc

    def _ffmpeg_source(self, stream_url: str) -> discord.AudioSource:
        ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")
        return discord.FFmpegPCMAudio(
            stream_url,
            executable=ffmpeg_path,
            before_options="-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn -loglevel warning",
        )

    async def enqueue(self, interaction: discord.Interaction, query: str) -> tuple[Track, int, bool]:
        if interaction.guild is None:
            raise RuntimeError("Music works only inside a server.")

        vc = await self.connect_to_author(interaction)
        track = await asyncio.to_thread(self._extract_track_sync, query)
        track.requested_by = interaction.user.display_name

        state = self.state_for(interaction.guild.id)
        state.queue.append(track)
        position = len(state.queue)
        should_start = state.current is None and not vc.is_playing() and not vc.is_paused()

        if should_start:
            await self._play_next(interaction.guild)

        return track, position, should_start

    async def _play_next(self, guild: discord.Guild) -> None:
        vc = guild.voice_client
        state = self.state_for(guild.id)

        if vc is None:
            state.current = None
            return

        if vc.is_playing() or vc.is_paused():
            return

        if not state.queue:
            state.current = None
            return

        track = state.queue.popleft()
        state.current = track
        source = self._ffmpeg_source(track.stream_url)
        loop = self.bot.loop

        def after_play(error: Exception | None) -> None:
            asyncio.run_coroutine_threadsafe(self._after_track(guild, error), loop)

        vc.play(source, after=after_play)

    async def _after_track(self, guild: discord.Guild, error: Exception | None) -> None:
        state = self.state_for(guild.id)
        finished = state.current

        if error:
            log.warning("Music playback error: %s", error)

        if state.loop_enabled and finished is not None:
            state.queue.appendleft(finished)

        state.current = None
        await asyncio.sleep(0.25)
        await self._play_next(guild)

    async def skip(self, guild: discord.Guild) -> str:
        vc = guild.voice_client
        if vc is None or not vc.is_connected():
            raise RuntimeError("Bot is not in a voice channel.")

        current = self.state_for(guild.id).current
        if not vc.is_playing():
            raise RuntimeError("No track is currently playing.")

        vc.stop()
        return current.title if current else "current track"

    async def stop(self, guild: discord.Guild) -> None:
        vc = guild.voice_client
        if vc is None or not vc.is_connected():
            raise RuntimeError("Bot is not in a voice channel.")

        state = self.state_for(guild.id)
        state.queue.clear()
        state.current = None

        if vc.is_playing() or vc.is_paused():
            vc.stop()

    async def toggle_loop(self, guild: discord.Guild) -> bool:
        state = self.state_for(guild.id)
        state.loop_enabled = not state.loop_enabled
        return state.loop_enabled
