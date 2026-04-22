from __future__ import annotations

import logging

import discord

log = logging.getLogger(__name__)


class VoiceAfkManager:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    def guild_voice_client(self, guild: discord.Guild | None) -> discord.VoiceClient | None:
        return guild.voice_client if guild else None

    async def connect_or_move_afk(self, interaction: discord.Interaction) -> discord.VoiceClient:
        return await self._connect_or_move(interaction, afk=True)

    async def connect_or_move_live(self, interaction: discord.Interaction) -> discord.VoiceClient:
        return await self._connect_or_move(interaction, afk=False)

    async def _connect_or_move(self, interaction: discord.Interaction, *, afk: bool) -> discord.VoiceClient:
        if interaction.guild is None:
            raise RuntimeError('Voice commands work only inside a server.')
        voice_state = getattr(interaction.user, 'voice', None)
        if voice_state is None or voice_state.channel is None:
            raise RuntimeError('Join a voice channel first.')
        target = voice_state.channel
        existing = self.guild_voice_client(interaction.guild)
        if existing and existing.channel and existing.channel.id != target.id:
            await existing.move_to(target)
            await self._apply_state(interaction.guild, target, afk=afk)
            return existing
        if existing and existing.channel and existing.channel.id == target.id:
            await self._apply_state(interaction.guild, target, afk=afk)
            return existing

        vc = await target.connect()
        await self._apply_state(interaction.guild, target, afk=afk)
        return vc

    async def _apply_state(self, guild: discord.Guild, channel: discord.abc.Connectable, *, afk: bool) -> None:
        try:
            await guild.change_voice_state(channel=channel, self_mute=afk, self_deaf=afk)
        except Exception:
            log.debug('Could not update self-mute/deafen state in voice mode.', exc_info=True)

    async def disconnect(self, guild: discord.Guild) -> None:
        vc = self.guild_voice_client(guild)
        if vc is None:
            raise RuntimeError('Bot is not in a voice channel.')
        await vc.disconnect(force=True)

    def snapshot(self, guild: discord.Guild | None) -> dict[str, object]:
        vc = self.guild_voice_client(guild)
        if vc and vc.channel:
            return {
                'connected': True,
                'channel_name': getattr(vc.channel, 'name', 'voice'),
                'guild_name': guild.name if guild else 'unknown',
                'afk_style': 'silent afk' if getattr(vc, 'self_deaf', False) or getattr(vc, 'self_mute', False) else 'live playback',
            }
        return {
            'connected': False,
            'channel_name': None,
            'guild_name': guild.name if guild else 'unknown',
            'afk_style': 'idle',
        }
