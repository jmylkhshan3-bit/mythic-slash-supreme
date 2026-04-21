from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands

from bot.config import Settings
from bot.logger import setup_logging
from bot.services.assets import AssetManager
from bot.services.elevenlabs_client import ElevenLabsClient
from bot.services.openrouter_client import OpenRouterClient
from bot.services.status_manager import PresenceManager
from bot.services.tts_service import TTSService
from bot.services.voice_runtime import VoiceRuntimeManager
from bot.state import GuildStateManager

log = logging.getLogger(__name__)


class MythicBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = settings.enable_mention_reply
        intents.messages = True
        intents.guilds = True
        intents.voice_states = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.settings = settings
        self.state_manager = GuildStateManager(Path('data/guild_state.json'))
        self.openrouter_client = OpenRouterClient(settings.openrouter_api_key, settings.openrouter_model)
        self.elevenlabs_client = ElevenLabsClient(
            settings.elevenlabs_api_key,
            settings.elevenlabs_voice_id,
            settings.elevenlabs_tts_model_id,
            settings.elevenlabs_stt_model_id,
            en_voice_id=settings.elevenlabs_en_voice_id,
            ar_voice_id=settings.elevenlabs_ar_voice_id,
        )
        self.tts_service = TTSService(elevenlabs_client=self.elevenlabs_client)
        self.asset_manager = AssetManager(settings.internal_assets_dir, settings.external_assets_dir)
        self.presence_manager = PresenceManager(self, settings.default_mode)
        self.voice_runtime = VoiceRuntimeManager(
            bot=self,
            settings=settings,
            state_manager=self.state_manager,
            openrouter_client=self.openrouter_client,
            elevenlabs_client=self.elevenlabs_client,
            tts_service=self.tts_service,
        )

    async def setup_hook(self) -> None:
        await self.load_extension('bot.cogs.mythic')
        synced = await self.tree.sync()
        log.info('Synced %s slash command(s)', len(synced))
        self.presence_manager.rotate.start()

    async def on_ready(self) -> None:
        if self.user:
            log.info('Logged in as %s (%s)', self.user, self.user.id)
            if self.settings.enable_mention_reply:
                log.info('Mention replies are enabled; Message Content Intent must also be enabled in the Dev Portal.')
            else:
                log.info('Mention replies are disabled.')
            if self.voice_runtime.receive_supported:
                log.info('Wake-word voice capture backend is available.')
            else:
                log.info('Wake-word voice capture backend is not available in this runtime.')

    async def on_command_error(self, context: commands.Context, exception: commands.CommandError) -> None:
        if isinstance(exception, commands.CommandNotFound):
            log.debug('Ignored legacy message command miss for: %s', context.message.content[:120] if context.message else '')
            return
        await super().on_command_error(context, exception)


async def run_bot() -> None:
    settings = Settings.load()
    setup_logging(settings.log_level)
    if not settings.discord_token:
        raise RuntimeError('DISCORD_TOKEN is missing. Fill .env first.')
    if not settings.openrouter_api_key:
        raise RuntimeError('OPENROUTER_API_KEY is missing. Fill .env first.')
    if not settings.elevenlabs_api_key:
        raise RuntimeError('ELEVENLABS_API_KEY is missing. Fill .env first.')
    bot = MythicBot(settings)
    async with bot:
        await bot.start(settings.discord_token)
