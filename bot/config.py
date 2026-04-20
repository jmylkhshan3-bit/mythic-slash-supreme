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
    assemblyai_api_key: str
    external_assets_dir: Path | None
    internal_assets_dir: Path
    default_mode: str
    log_level: str
    enable_mention_reply: bool
    activation_phrase: str
    tts_voice_ar: str
    tts_voice_en: str
    voice_silence_seconds: float
    voice_trigger_level_db: float
    enable_experimental_voice_recv: bool

    @classmethod
    def load(cls) -> 'Settings':
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(dotenv_path=project_root / '.env')
        assets_raw = os.getenv('EXTERNAL_ASSETS_DIR', '').strip()
        assets_path = Path(assets_raw).expanduser().resolve() if assets_raw else None
        def _to_float(name: str, default: float) -> float:
            raw = os.getenv(name, str(default)).strip()
            try:
                return float(raw)
            except ValueError:
                return default
        return cls(
            discord_token=os.getenv('DISCORD_TOKEN', '').strip(),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY', '').strip(),
            openrouter_model=os.getenv('OPENROUTER_MODEL', 'openrouter/free').strip(),
            assemblyai_api_key=os.getenv('ASSEMBLYAI_API_KEY', '').strip(),
            external_assets_dir=assets_path,
            internal_assets_dir=project_root / 'bot_ui',
            default_mode=os.getenv('DEFAULT_MODE', 'normal').strip().lower(),
            log_level=os.getenv('LOG_LEVEL', 'INFO').strip().upper(),
            enable_mention_reply=os.getenv('ENABLE_MENTION_REPLY', 'true').strip().lower() in {'1', 'true', 'yes', 'on'},
            activation_phrase=os.getenv('ACTIVATION_PHRASE', 'hey m').strip().lower(),
            tts_voice_ar=os.getenv('TTS_VOICE_AR', 'ar-SA-HamedNeural').strip(),
            tts_voice_en=os.getenv('TTS_VOICE_EN', 'en-US-AndrewNeural').strip(),
            voice_silence_seconds=_to_float('VOICE_SILENCE_SECONDS', 2.0),
            voice_trigger_level_db=_to_float('VOICE_TRIGGER_LEVEL_DB', -42.0),
            enable_experimental_voice_recv=os.getenv('ENABLE_EXPERIMENTAL_VOICE_RECV', 'true').strip().lower() in {'1', 'true', 'yes', 'on'},
        )
