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
except Exception:  # pragma: no cover - optional dependency
    voice_recv = None

if TYPE_CHECKING:
    from bot.config import Settings
    from bot.services.assemblyai_client import AssemblyAIClient
    from bot.services.openrouter_client import OpenRouterClient
    from bot.services.tts_service import TTSService
    from bot.state import GuildStateManager

log = logging.getLogger(__name__)
_NORMALIZE_RE = re.compile(r'[^\w\s\u0600-\u06FF]+', re.UNICODE)


@dataclass(slots=True)
class VoiceRuntimeSnapshot:
    connected_channel: str | None
    armed: bool
    receive_supported: bool
    receive_active: bool
    runtime_mode: str
    note: str


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
    armed: bool = False
    sink: object | None = None
    monitor_task: asyncio.Task | None = None
    users: dict[int, UserAudioState] = field(default_factory=dict)
    processing_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    bot_speaking: bool = False
    last_transcript: str = ''


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
        self.manager.feed_pcm(self.guild_id, int(user.id), getattr(user, 'display_name', getattr(user, 'name', str(user.id))), bytes(data.pcm))

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
        assemblyai_client: 'AssemblyAIClient',
        tts_service: 'TTSService',
    ) -> None:
        self.bot = bot
        self.settings = settings
        self.state_manager = state_manager
        self.openrouter_client = openrouter_client
        self.assemblyai_client = assemblyai_client
        self.tts_service = tts_service
        self._sessions: dict[int, GuildVoiceSession] = {}

    @property
    def receive_supported(self) -> bool:
        return bool(self.settings.enable_experimental_voice_recv and voice_recv is not None)

    @property
    def runtime_mode(self) -> str:
        return 'official-bot'

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

        if existing and existing.channel and existing.channel.id == target.id:
            if self.receive_supported and not hasattr(existing, 'listen'):
                await existing.disconnect(force=True)
            else:
                if session.armed:
                    await self._ensure_listener(interaction.guild, existing)
                return existing

        if existing and existing.channel:
            if self.receive_supported and not hasattr(existing, 'listen'):
                await existing.disconnect(force=True)
            else:
                await existing.move_to(target)
                if session.armed:
                    await self._ensure_listener(interaction.guild, existing)
                return existing

        if self.receive_supported:
            vc = await target.connect(cls=voice_recv.VoiceRecvClient)
        else:
            vc = await target.connect()
        if session.armed:
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

    async def arm(self, guild: discord.Guild | None, *, text_channel_id: int | None = None) -> str:
        if guild is None:
            raise RuntimeError('Voice arm works only inside a server.')
        vc = self.guild_voice_client(guild)
        if vc is None:
            raise RuntimeError('Join a voice channel with the bot first.')
        session = self._session(guild.id)
        session.armed = True
        if text_channel_id is not None:
            session.text_channel_id = text_channel_id
        if self.receive_supported:
            await self._ensure_listener(guild, vc)
            return 'Voice runtime armed. قل hey m ثم طلبك بصوت واحد أو على دفعتين، وسيتوقف التسجيل تلقائيًا عند الصمت.'
        return 'Voice runtime armed in compatibility mode, but live receive backend is unavailable in this runtime.'

    async def disarm(self, guild: discord.Guild | None) -> str:
        if guild is None:
            raise RuntimeError('Voice disarm works only inside a server.')
        session = self._sessions.get(guild.id)
        if session:
            session.armed = False
            for user_state in session.users.values():
                user_state.frames.clear()
                user_state.awaiting_followup_until = 0.0
        vc = self.guild_voice_client(guild)
        if vc and hasattr(vc, 'stop_listening'):
            try:
                vc.stop_listening()
            except Exception:
                pass
        if session:
            session.sink = None
        return 'Voice runtime disarmed.'

    async def speak_text(self, guild: discord.Guild | None, text: str, *, preferred_language: str | None = None) -> str:
        if guild is None:
            raise RuntimeError('Voice speak works only inside a server.')
        vc = self.guild_voice_client(guild)
        if vc is None:
            raise RuntimeError('The bot is not connected to a voice channel.')
        session = self._session(guild.id)
        await self._play_reply(session, vc, text, preferred_language=preferred_language)
        return vc.channel.name if vc.channel else 'voice'

    def feed_pcm(self, guild_id: int, user_id: int, display_name: str, pcm: bytes) -> None:
        try:
            loop = self.bot.loop
            loop.call_soon_threadsafe(self._feed_pcm_sync, guild_id, user_id, display_name, pcm)
        except RuntimeError:
            pass

    def _feed_pcm_sync(self, guild_id: int, user_id: int, display_name: str, pcm: bytes) -> None:
        session = self._sessions.get(guild_id)
        if session is None or not session.armed or session.bot_speaking:
            return
        state = self.state_manager.get(guild_id)
        level = self._pcm_dbfs(pcm)
        if level < float(state.get('voice_trigger_level_db', self.settings.voice_trigger_level_db)):
            return
        user_state = session.users.setdefault(user_id, UserAudioState(display_name=display_name))
        user_state.display_name = display_name
        user_state.frames.extend(pcm)
        user_state.last_sound_at = time.monotonic()

    async def _ensure_listener(self, guild: discord.Guild, vc: discord.VoiceClient) -> None:
        if not self.receive_supported:
            return
        if not hasattr(vc, 'listen'):
            raise RuntimeError('Live voice receive is not available on this voice connection.')
        session = self._session(guild.id)
        if session.monitor_task is None or session.monitor_task.done():
            session.monitor_task = asyncio.create_task(self._monitor_loop(guild.id), name=f'mythic_voice_monitor_{guild.id}')
        if getattr(vc, 'is_listening', lambda: False)():
            return
        session.sink = LiveCaptureSink(self, guild.id)
        vc.listen(session.sink)

    async def _monitor_loop(self, guild_id: int) -> None:
        try:
            while True:
                await asyncio.sleep(0.4)
                session = self._sessions.get(guild_id)
                if session is None:
                    return
                if not session.armed:
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
        guild = self.bot.get_guild(guild_id)
        session = self._session(guild_id)
        async with session.processing_lock:
            state = self.state_manager.get(guild_id)
            transcript = await self._transcribe_pcm(pcm, state)
            if not transcript or not transcript.text.strip():
                return
            text = transcript.text.strip()
            session.last_transcript = text
            command = self._extract_voice_command(guild_id, user_id, text)
            if command is None:
                return
            if not command:
                await self._send_text_update(guild_id, f'🎧 **{display_name}**: تم تفعيل {state.get("voice_wake_phrase", self.settings.activation_phrase)}. قل الطلب الآن.')
                return
            try:
                reply = await self.openrouter_client.chat(
                    prompt=command,
                    mode=state.get('mode', 'normal'),
                    user_name=display_name,
                    guild_name=guild.name if guild else None,
                    system_note=state.get('system_note', ''),
                )
            except Exception as exc:
                await self._send_text_update(guild_id, f'AI request failed: {exc}')
                return
            await self._send_voice_reply(guild_id, display_name, text, reply, state)

    async def _transcribe_pcm(self, pcm: bytes, state: dict):
        if not self.assemblyai_client.enabled:
            raise RuntimeError('ASSEMBLYAI_API_KEY is missing.')
        wav_bytes = self._pcm_to_wav_bytes(pcm)
        input_lang = str(state.get('voice_input_language', 'auto')).lower().strip()
        language_code = None
        language_detection = True
        expected_languages = ['ar', 'en']
        if input_lang in {'ar', 'arabic'}:
            language_code = 'ar'
            language_detection = False
        elif input_lang in {'en', 'english'}:
            language_code = 'en'
            language_detection = False
        return await self.assemblyai_client.transcribe_bytes(
            data=wav_bytes,
            speaker_labels=False,
            language_detection=language_detection,
            language_code=language_code,
            expected_languages=expected_languages,
        )

    def _extract_voice_command(self, guild_id: int, user_id: int, text: str) -> str | None:
        session = self._session(guild_id)
        user_state = session.users.setdefault(user_id, UserAudioState(display_name='User'))
        phrase = str(self.state_manager.get(guild_id).get('voice_wake_phrase', self.settings.activation_phrase)).lower().strip()
        lowered = text.lower()
        if user_state.awaiting_followup_until > time.monotonic():
            user_state.awaiting_followup_until = 0.0
            return text.strip()
        index = lowered.find(phrase)
        if index == -1:
            return None
        command = text[index + len(phrase):].strip(' :,-')
        if command:
            return command
        user_state.awaiting_followup_until = time.monotonic() + 12.0
        return ''

    async def _send_voice_reply(self, guild_id: int, display_name: str, transcript_text: str, reply: str, state: dict) -> None:
        reply_mode = str(state.get('voice_reply_mode', 'voice+text')).lower()
        if reply_mode in {'voice+text', 'text'}:
            text_message = (
                f'🎙️ **{display_name}**\n> {transcript_text}\n\n'
                f'🤖 **Mythic**\n{reply[:1800]}'
            )
            await self._send_text_update(guild_id, text_message)
        if reply_mode in {'voice+text', 'voice'}:
            guild = self.bot.get_guild(guild_id)
            vc = self.guild_voice_client(guild)
            if vc is not None:
                preferred = str(state.get('voice_output_language', 'auto')).lower()
                if preferred not in {'ar', 'en'}:
                    preferred = None
                session = self._session(guild_id)
                await self._play_reply(session, vc, reply, preferred_language=preferred)

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

    async def _play_reply(self, session: GuildVoiceSession, vc: discord.VoiceClient, text: str, *, preferred_language: str | None = None) -> None:
        if vc.is_playing():
            vc.stop()
        audio_path = await self.tts_service.synthesize(text, preferred=preferred_language)
        session.bot_speaking = True
        done = asyncio.Event()
        ffmpeg_executable = resolve_ffmpeg_executable()
        source = discord.FFmpegPCMAudio(str(audio_path), executable=ffmpeg_executable)

        def _after(exc: Exception | None) -> None:
            def _finish() -> None:
                session.bot_speaking = False
                try:
                    audio_path.unlink(missing_ok=True)
                except Exception:
                    pass
                if exc:
                    log.error('Voice playback error: %s', exc)
                done.set()

            self.bot.loop.call_soon_threadsafe(_finish)

        vc.play(source, after=_after)
        await done.wait()

    def snapshot(self, guild: discord.Guild | None, state: dict) -> VoiceRuntimeSnapshot:
        vc = self.guild_voice_client(guild)
        channel_name = vc.channel.name if vc and vc.channel else None
        session = self._sessions.get(guild.id) if guild else None
        receive_active = bool(session and session.armed and vc and getattr(vc, 'is_listening', lambda: False)())
        note = 'Official bot runtime. After arming, the bot waits for the wake phrase, records until silence, transcribes, asks the AI, then speaks back.'
        if not self.receive_supported:
            note += ' Live receive backend is unavailable in this runtime, so wake-word listening cannot start yet.'
        elif session and session.last_transcript:
            note += f' Last transcript: {session.last_transcript[:140]}'
        return VoiceRuntimeSnapshot(
            connected_channel=channel_name,
            armed=bool(state.get('voice_armed', False)),
            receive_supported=self.receive_supported,
            receive_active=receive_active,
            runtime_mode=self.runtime_mode,
            note=note,
        )

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
