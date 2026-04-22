from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands

from bot.config import Settings
from bot.logger import setup_logging
from bot.services.assets import AssetManager
from bot.services.music_service import MusicService
from bot.services.openrouter_client import OpenRouterClient
from bot.services.status_manager import PresenceManager
from bot.services.voice_afk_manager import VoiceAfkManager
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
        self.asset_manager = AssetManager(settings.internal_assets_dir, settings.external_assets_dir)
        self.presence_manager = PresenceManager(self, settings.default_mode)
        self.voice_afk_manager = VoiceAfkManager(self)
        self.music_service = MusicService(self)

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
            log.info('Voice AFK mode and YouTube audio playback are available in this build.')

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
    bot = MythicBot(settings)
    async with bot:
        await bot.start(settings.discord_token)
