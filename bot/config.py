from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    discord_token: str
    openrouter_api_key: str
    openrouter_model: str
    external_assets_dir: Path | None
    internal_assets_dir: Path
    default_mode: str
    log_level: str
    enable_mention_reply: bool
    sync_guild_id: int | None

    @classmethod
    def load(cls) -> 'Settings':
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(dotenv_path=project_root / '.env')
        assets_raw = os.getenv('EXTERNAL_ASSETS_DIR', '').strip()
        assets_path = Path(assets_raw).expanduser().resolve() if assets_raw else None
        sync_guild = os.getenv('SYNC_GUILD_ID', '').strip()
        return cls(
            discord_token=os.getenv('DISCORD_TOKEN', '').strip(),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY', '').strip(),
            openrouter_model=os.getenv('OPENROUTER_MODEL', 'google/gemma-3-4b-it:free').strip(),
            external_assets_dir=assets_path,
            internal_assets_dir=project_root / 'bot_ui',
            default_mode=os.getenv('DEFAULT_MODE', 'normal').strip().lower(),
            log_level=os.getenv('LOG_LEVEL', 'INFO').strip().upper(),
            enable_mention_reply=os.getenv('ENABLE_MENTION_REPLY', 'true').strip().lower() in {'1', 'true', 'yes', 'on'},
            sync_guild_id=int(sync_guild) if sync_guild.isdigit() else None,
        )
