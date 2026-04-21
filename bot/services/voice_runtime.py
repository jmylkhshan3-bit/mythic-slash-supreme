from __future__ import annotations

import asyncio
import io
import logging
import math
import re
import time
import wave
from array import array
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import discord

from bot.services.ffmpeg_utils import resolve_ffmpeg_executable

try:
    from discord.ext import voice_recv
except Exception:  # pragma: no cover
    voice_recv = None

if TYPE_CHECKING:
    from bot.config import Settings
    from bot.services.elevenlabs_client import ElevenLabsClient, TranscriptResult
    from bot.services.music_service import MusicManager
    from bot.services.openrouter_client import OpenRouterClient
    from bot.services.tts_service import TTSService
    from bot.state import GuildStateManager

log = logging.getLogger(__name__)
_NORMALIZE_RE = re.compile(r'[^\w\s]+', re.UNICODE)
_ARABIC_RE = re.compile(r'[\u0600-\u06FF]')


@dataclass(slots=True)
class VoiceRuntimeSnapshot:
    connected_channel: str | None
    receive_supported: bool
    receive_active: bool
    note: str
    last_transcript: str


@dataclass(slots=True)
class UserAudioState:
    display_name: str
    frames: bytearray = field(default_factory=bytearray)
    last_sound_at: float = 0.0
    awaiting_followup_until: float = 0.0


@dataclass(slots=True)
class GuildVoiceSession:
    guild_id: int
    text_channel_id: int | None = None
    sink: object | None = None
    monitor_task: asyncio.Task | None = None
    users: dict[int, UserAudioState] = field(default_factory=dict)
    processing_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    playback_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    playback_task: asyncio.Task | None = None
    bot_speaking: bool = False
    last_transcript: str = ''
    listener_started: bool = False


class LiveCaptureSink(voice_recv.AudioSink if voice_recv is not None else object):
    def __init__(self, manager: 'VoiceRuntimeManager', guild_id: int):
        if voice_recv is None:
            raise RuntimeError('voice receive backend is not available')
        super().__init__()
        self.manager = manager
        self.guild_id = guild_id

    def wants_opus(self) -> bool:
        return False

    def write(self, user, data) -> None:
        if user is None or getattr(user, 'bot', False) or not getattr(data, 'pcm', None):
            return
        self.manager.feed_pcm(
            self.guild_id,
            int(user.id),
            getattr(user, 'display_name', getattr(user, 'name', str(user.id))),
            bytes(data.pcm),
        )

    def cleanup(self) -> None:
        return None


class VoiceRuntimeManager:
    def __init__(
        self,
        *,
        bot: discord.Client,
        settings: 'Settings',
        state_manager: 'GuildStateManager',
        openrouter_client: 'OpenRouterClient',
        elevenlabs_client: 'ElevenLabsClient',
        tts_service: 'TTSService',
        music_manager: 'MusicManager',
    ) -> None:
        self.bot = bot
        self.settings = settings
        self.state_manager = state_manager
        self.openrouter_client = openrouter_client
        self.elevenlabs_client = elevenlabs_client
        self.tts_service = tts_service
        self.music_manager = music_manager
        self._sessions: dict[int, GuildVoiceSession] = {}

    @property
    def receive_supported(self) -> bool:
        return bool(self.settings.enable_experimental_voice_recv and voice_recv is not None)

    def guild_voice_client(self, guild: discord.Guild | None) -> discord.VoiceClient | None:
        return guild.voice_client if guild else None

    def _session(self, guild_id: int) -> GuildVoiceSession:
        session = self._sessions.get(guild_id)
        if session is None:
            session = GuildVoiceSession(guild_id=guild_id)
            self._sessions[guild_id] = session
        return session

    async def connect_or_move(self, interaction: discord.Interaction) -> discord.VoiceClient:
        if interaction.guild is None:
            raise RuntimeError('Voice features work only inside a server.')
        voice_state = getattr(interaction.user, 'voice', None)
        if voice_state is None or voice_state.channel is None:
            raise RuntimeError('Join a voice channel first.')
        target = voice_state.channel
        existing = self.guild_voice_client(interaction.guild)
        session = self._session(interaction.guild.id)
        session.text_channel_id = interaction.channel_id

        if existing and existing.channel and existing.channel.id != target.id:
            await existing.move_to(target)
            await self._ensure_listener(interaction.guild, existing)
            return existing
        if existing and existing.channel and existing.channel.id == target.id:
            await self._ensure_listener(interaction.guild, existing)
            return existing

        if self.receive_supported:
            vc = await target.connect(cls=voice_recv.VoiceRecvClient)
        else:
            vc = await target.connect()
        await self._ensure_listener(interaction.guild, vc)
        return vc

    async def disconnect(self, guild: discord.Guild | None) -> None:
        if guild is None:
            return
        session = self._sessions.get(guild.id)
        if session and session.monitor_task:
            session.monitor_task.cancel()
        vc = self.guild_voice_client(guild)
        if vc and hasattr(vc, 'stop_listening'):
            try:
                vc.stop_listening()
            except Exception:
                pass
        if vc:
            await vc.disconnect(force=True)
        self._sessions.pop(guild.id, None)

    async def speak_text(self, guild: discord.Guild | None, text: str, *, preferred_language: str | None = None) -> str:
        if guild is None:
            raise RuntimeError('Speak works only inside a server.')
        vc = self.guild_voice_client(guild)
        if vc is None:
            raise RuntimeError('The bot is not connected to a voice channel.')
        session = self._session(guild.id)
        resolved_language = preferred_language or self._infer_language_from_text(text)
        await self._play_reply(session, vc, text, preferred_language=resolved_language, wait_for_finish=False)
        return vc.channel.name if vc.channel else 'voice'

    def feed_pcm(self, guild_id: int, user_id: int, display_name: str, pcm: bytes) -> None:
        try:
            self.bot.loop.call_soon_threadsafe(self._feed_pcm_sync, guild_id, user_id, display_name, pcm)
        except RuntimeError:
            return

    def _feed_pcm_sync(self, guild_id: int, user_id: int, display_name: str, pcm: bytes) -> None:
        session = self._sessions.get(guild_id)
        if session is None or self.music_manager.is_playing(guild_id) or session.bot_speaking:
            return
        level = self._pcm_dbfs(pcm)
        state = self.state_manager.get(guild_id)
        if level < float(state.get('voice_trigger_level_db', self.settings.voice_trigger_level_db)):
            return
        user_state = session.users.setdefault(user_id, UserAudioState(display_name=display_name))
        user_state.display_name = display_name
        user_state.frames.extend(pcm)
        user_state.last_sound_at = time.monotonic()

    async def _ensure_listener(self, guild: discord.Guild, vc: discord.VoiceClient) -> None:
        session = self._session(guild.id)
        if session.monitor_task is None or session.monitor_task.done():
            session.monitor_task = asyncio.create_task(self._monitor_loop(guild.id), name=f'mythic_voice_monitor_{guild.id}')
        if not self.receive_supported or not hasattr(vc, 'listen'):
            return
        if getattr(vc, 'is_listening', lambda: False)():
            session.listener_started = True
            return
        session.sink = LiveCaptureSink(self, guild.id)
        vc.listen(session.sink)
        session.listener_started = True

    async def _monitor_loop(self, guild_id: int) -> None:
        try:
            while True:
                await asyncio.sleep(0.5)
                session = self._sessions.get(guild_id)
                if session is None:
                    return
                if self.music_manager.is_playing(guild_id):
                    continue
                state = self.state_manager.get(guild_id)
                silence_seconds = float(state.get('voice_silence_seconds', self.settings.voice_silence_seconds))
                now = time.monotonic()
                for user_id, user_state in list(session.users.items()):
                    if not user_state.frames:
                        continue
                    if user_state.last_sound_at and now - user_state.last_sound_at >= silence_seconds:
                        pcm = bytes(user_state.frames)
                        user_state.frames.clear()
                        asyncio.create_task(
                            self._process_utterance(guild_id, user_id, user_state.display_name, pcm),
                            name=f'mythic_utterance_{guild_id}_{user_id}',
                        )
        except asyncio.CancelledError:
            return

    async def _process_utterance(self, guild_id: int, user_id: int, display_name: str, pcm: bytes) -> None:
        if self._pcm_duration_seconds(pcm) < 0.45:
            return
        session = self._session(guild_id)
        async with session.processing_lock:
            state = self.state_manager.get(guild_id)
            transcript = await self._transcribe_pcm(pcm, state)
            text = (transcript.text or '').strip()
            if not text:
                return
            session.last_transcript = text
            command = self._extract_voice_command(guild_id, user_id, text)
            if command is None:
                return
            if not command:
                await self._send_text_update(guild_id, f'🎧 Wake phrase detected for **{display_name}**. Listening for the request...')
                return
            guild = self.bot.get_guild(guild_id)
            reply_language = self._resolve_reply_language(command, transcript.language_code, state)
            try:
                reply = await self.openrouter_client.chat(
                    prompt=command,
                    mode=state.get('mode', 'normal'),
                    user_name=display_name,
                    guild_name=guild.name if guild else None,
                    system_note=state.get('system_note', ''),
                    preferred_reply_language=reply_language,
                )
            except Exception as exc:
                await self._send_text_update(guild_id, f'AI request failed: {exc}')
                return
            await self._send_voice_reply(guild_id, display_name, text, reply, reply_language)

    async def _transcribe_pcm(self, pcm: bytes, state: dict) -> 'TranscriptResult':
        language = str(state.get('voice_input_language', 'auto')).lower().strip()
        if language not in {'en', 'ar', 'auto'}:
            language = 'auto'
        wav_bytes = self._pcm_to_wav_bytes(pcm)
        return await self.elevenlabs_client.speech_to_text(
            data=wav_bytes,
            filename='voice_capture.wav',
            language_code=None if language == 'auto' else language,
        )

    def _extract_voice_command(self, guild_id: int, user_id: int, text: str) -> str | None:
        session = self._session(guild_id)
        user_state = session.users.setdefault(user_id, UserAudioState(display_name='User'))
        phrase = str(self.state_manager.get(guild_id).get('voice_wake_phrase', self.settings.activation_phrase)).lower().strip()
        normalized = self.normalize_text(text)
        if user_state.awaiting_followup_until > time.monotonic():
            user_state.awaiting_followup_until = 0.0
            return text.strip()

        aliases = self._wake_aliases(phrase)
        matched_alias = None
        for alias in aliases:
            alias_n = self.normalize_text(alias)
            if not alias_n:
                continue
            idx = normalized.find(alias_n)
            if idx != -1:
                matched_alias = alias
                break
        if matched_alias is None:
            return None

        raw_index = text.lower().find(matched_alias.lower())
        if raw_index == -1:
            # fallback to consume the beginning if STT spacing/punctuation differs
            raw_index = 0
        command = text[raw_index + len(matched_alias):].strip(' :,-')
        if command:
            return command
        user_state.awaiting_followup_until = time.monotonic() + 12.0
        return ''

    async def _send_voice_reply(
        self,
        guild_id: int,
        display_name: str,
        transcript_text: str,
        reply: str,
        reply_language: str | None,
    ) -> None:
        lang_label = 'Arabic' if (reply_language or '').startswith('ar') else 'English'
        await self._send_text_update(guild_id, f'🎙️ **{display_name}**\n> {transcript_text}\n\n🤖 **Mythic ({lang_label})**\n{reply[:1800]}')
        guild = self.bot.get_guild(guild_id)
        vc = self.guild_voice_client(guild)
        if vc is None:
            return
        session = self._session(guild_id)
        await self._play_reply(session, vc, reply, preferred_language=reply_language, wait_for_finish=True)

    async def _send_text_update(self, guild_id: int, content: str) -> None:
        session = self._sessions.get(guild_id)
        if session is None or session.text_channel_id is None:
            return
        channel = self.bot.get_channel(session.text_channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(session.text_channel_id)
            except Exception:
                return
        if isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
            try:
                await channel.send(content[:1950])
            except Exception:
                log.exception('Failed sending voice text update')

    async def _play_reply(
        self,
        session: GuildVoiceSession,
        vc: discord.VoiceClient,
        text: str,
        *,
        preferred_language: str | None = None,
        wait_for_finish: bool = True,
    ) -> None:
        async with session.playback_lock:
            if session.playback_task and not session.playback_task.done():
                session.playback_task.cancel()
            if vc.is_playing() or vc.is_paused():
                vc.stop()
                await asyncio.sleep(0.35)

            audio_path = await self.tts_service.synthesize(text, preferred=preferred_language)
            if not audio_path.exists() or audio_path.stat().st_size <= 512:
                raise RuntimeError('The generated audio file is invalid or empty.')

            session.bot_speaking = True
            done = asyncio.Event()
            playback_error: dict[str, Exception | None] = {'error': None}
            ffmpeg_executable = resolve_ffmpeg_executable()
            source = discord.FFmpegPCMAudio(
                str(audio_path),
                executable=ffmpeg_executable,
                before_options='-nostdin -hide_banner -loglevel error',
                options='-vn',
            )

            def _after(exc: Exception | None) -> None:
                def _finish() -> None:
                    session.bot_speaking = False
                    playback_error['error'] = exc
                    done.set()
                self.bot.loop.call_soon_threadsafe(_finish)

            try:
                vc.play(source, after=_after)
            except Exception:
                session.bot_speaking = False
                try:
                    audio_path.unlink(missing_ok=True)
                except Exception:
                    pass
                raise

            started = False
            for _ in range(30):
                await asyncio.sleep(0.1)
                if vc.is_playing() or vc.is_paused():
                    started = True
                    break
                if done.is_set():
                    break

            if not started and playback_error['error'] is None and not done.is_set():
                try:
                    vc.stop()
                except Exception:
                    pass
                session.bot_speaking = False
                try:
                    audio_path.unlink(missing_ok=True)
                except Exception:
                    pass
                raise RuntimeError('Voice playback did not start. Check the bot voice permissions and ElevenLabs output.')

            async def _wait_and_cleanup() -> None:
                try:
                    await done.wait()
                    if playback_error['error']:
                        raise RuntimeError(f'Voice playback error: {playback_error["error"]}')
                finally:
                    try:
                        audio_path.unlink(missing_ok=True)
                    except Exception:
                        pass

            session.playback_task = asyncio.create_task(_wait_and_cleanup(), name=f'mythic_playback_{session.guild_id}')
            if wait_for_finish:
                await session.playback_task

    def snapshot(self, guild: discord.Guild | None, state: dict) -> VoiceRuntimeSnapshot:
        vc = self.guild_voice_client(guild)
        channel_name = vc.channel.name if vc and vc.channel else None
        session = self._sessions.get(guild.id) if guild else None
        receive_active = bool(session and session.listener_started and vc)
        note = 'Bot listens for "hey m", captures speech after the wake phrase, transcribes with ElevenLabs, asks the AI, then speaks the answer in Arabic or English automatically.'
        if not self.receive_supported:
            note += ' Live receive backend is unavailable in this runtime.'
        return VoiceRuntimeSnapshot(
            connected_channel=channel_name,
            receive_supported=self.receive_supported,
            receive_active=receive_active,
            note=note,
            last_transcript=session.last_transcript[:140] if session and session.last_transcript else '',
        )

    @staticmethod
    def _wake_aliases(phrase: str) -> list[str]:
        aliases = [phrase]
        if phrase == 'hey m':
            aliases.extend(['hey em', 'hey m.', 'hey, m', 'heyเอ็ม'])
        return aliases

    @staticmethod
    def _normalize_language_code(language_code: str | None) -> str | None:
        if not language_code:
            return None
        code = language_code.lower().strip()
        if code in {'ar', 'ara', 'arabic'}:
            return 'ar'
        if code in {'en', 'eng', 'english'}:
            return 'en'
        return code

    @classmethod
    def _infer_language_from_text(cls, text: str) -> str:
        if _ARABIC_RE.search(text):
            return 'ar'
        return 'en'

    @classmethod
    def _resolve_reply_language(cls, command: str, transcript_language: str | None, state: dict) -> str:
        configured = str(state.get('voice_output_language', 'auto')).lower().strip()
        if configured in {'ar', 'en'}:
            return configured
        normalized = cls._normalize_language_code(transcript_language)
        if normalized in {'ar', 'en'}:
            return normalized
        return cls._infer_language_from_text(command)

    @staticmethod
    def _pcm_to_wav_bytes(pcm: bytes) -> bytes:
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(48000)
            wav_file.writeframes(pcm)
        return output.getvalue()

    @staticmethod
    def _pcm_duration_seconds(pcm: bytes) -> float:
        if not pcm:
            return 0.0
        return len(pcm) / (48000 * 2 * 2)

    @staticmethod
    def _pcm_dbfs(pcm: bytes) -> float:
        if not pcm:
            return -100.0
        try:
            samples = array('h')
            samples.frombytes(pcm[: len(pcm) - (len(pcm) % 2)])
            if not samples:
                return -100.0
            square_sum = 0.0
            for sample in samples:
                square_sum += float(sample) * float(sample)
            rms = math.sqrt(square_sum / len(samples))
            if rms <= 0.0:
                return -100.0
            return 20.0 * math.log10(rms / 32768.0)
        except Exception:
            return -100.0

    @staticmethod
    def normalize_text(text: str) -> str:
        normalized = _NORMALIZE_RE.sub(' ', text.lower())
        return re.sub(r'\s+', ' ', normalized).strip()
