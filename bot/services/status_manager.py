from __future__ import annotations

import random

import discord
from discord.ext import tasks

from bot.constants import MODE_PRESETS


class PresenceManager:
    def __init__(self, bot, default_mode: str) -> None:
        self.bot = bot
        self.mode = default_mode if default_mode in MODE_PRESETS else 'normal'

    def set_mode(self, mode: str) -> None:
        self.mode = mode if mode in MODE_PRESETS else 'normal'

    @tasks.loop(seconds=45)
    async def rotate(self) -> None:
        preset = MODE_PRESETS.get(self.mode, MODE_PRESETS['normal'])
        line = random.choice(preset.presence_lines)
        await self.bot.change_presence(
            activity=discord.CustomActivity(name=f'{preset.emoji} {line}'),
            status=discord.Status.online,
        )

    @rotate.before_loop
    async def before_rotate(self) -> None:
        await self.bot.wait_until_ready()
