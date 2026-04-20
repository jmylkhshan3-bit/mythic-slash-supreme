from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import discord

try:
    from discord.ext import voice_recv
except Exception:  # pragma: no cover - optional dependency
    voice_recv = None


@dataclass(slots=True)
class VoiceRuntimeSnapshot:
    connected_channel: str | None
    armed: bool
    receive_supported: bool
    receive_active: bool
    runtime_mode: str
    note: str


class VoiceRuntimeManager:
    def __init__(self, settings) -> None:
        self.settings = settings
        self._receive_active: dict[int, bool] = {}

    @property
    def receive_supported(self) -> bool:
        return bool(self.settings.enable_experimental_voice_recv and voice_recv is not None)

    @property
    def runtime_mode(self) -> str:
        return 'official-bot'

    def guild_voice_client(self, guild: discord.Guild | None) -> discord.VoiceClient | None:
        if guild is None:
            return None
        return discord.utils.get(guild._state._get_client().voice_clients, guild=guild)

    async def connect_or_move(self, interaction: discord.Interaction) -> discord.VoiceClient:
        if interaction.guild is None:
            raise RuntimeError('Voice features work only inside a server.')
        voice_state = getattr(interaction.user, 'voice', None)
        if voice_state is None or voice_state.channel is None:
            raise RuntimeError('Join a voice channel first.')
        existing = self.guild_voice_client(interaction.guild)
        target = voice_state.channel
        if existing and existing.channel and existing.channel.id == target.id:
            return existing
        if existing and existing.channel:
            await existing.move_to(target)
            return existing
        if self.receive_supported:
            return await target.connect(cls=voice_recv.VoiceRecvClient)
        return await target.connect()

    async def disconnect(self, guild: discord.Guild | None) -> None:
        vc = self.guild_voice_client(guild)
        if vc:
            await vc.disconnect(force=True)
        if guild is not None:
            self._receive_active[guild.id] = False

    async def arm(self, guild: discord.Guild | None) -> str:
        if guild is None:
            raise RuntimeError('Voice arm works only inside a server.')
        vc = self.guild_voice_client(guild)
        if vc is None:
            raise RuntimeError('Join a voice channel with the bot first.')
        if self.receive_supported and hasattr(vc, 'listen'):
            self._receive_active[guild.id] = True
            return 'Wake-word voice design is armed. The bot is ready to route live receive through the official bot runtime.'
        self._receive_active[guild.id] = False
        return 'Voice design is armed in compatibility mode. Live receive needs the experimental voice receive backend to be available at runtime.'

    async def disarm(self, guild: discord.Guild | None) -> str:
        if guild is None:
            raise RuntimeError('Voice disarm works only inside a server.')
        vc = self.guild_voice_client(guild)
        if vc and hasattr(vc, 'stop_listening'):
            try:
                vc.stop_listening()
            except Exception:
                pass
        self._receive_active[guild.id] = False
        return 'Wake-word voice design is disarmed.'

    def snapshot(self, guild: discord.Guild | None, state: dict) -> VoiceRuntimeSnapshot:
        vc = self.guild_voice_client(guild)
        channel_name = vc.channel.name if vc and vc.channel else None
        receive_active = bool(guild and self._receive_active.get(guild.id, False))
        note = (
            'Official bot runtime only. No main-account automation. Wake-word capture starts after connect and can stop on silence.'
        )
        if not self.receive_supported:
            note += ' Live receive backend is optional; the project falls back gracefully when it is unavailable.'
        return VoiceRuntimeSnapshot(
            connected_channel=channel_name,
            armed=bool(state.get('voice_armed', False)),
            receive_supported=self.receive_supported,
            receive_active=receive_active,
            runtime_mode=self.runtime_mode,
            note=note,
        )
