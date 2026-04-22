from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _parse_creator_ids() -> tuple[int, ...]:
    raw_values = [
        os.getenv('CREATOR_IDS', '').strip(),
        os.getenv('CREATOR_ID', '').strip(),
    ]
    ids: list[int] = []
    for raw in raw_values:
        if not raw:
            continue
        for piece in raw.replace(';', ',').split(','):
            piece = piece.strip()
            if piece.isdigit():
                ids.append(int(piece))
    # preserve order and uniqueness
    seen: set[int] = set()
    unique: list[int] = []
    for cid in ids:
        if cid not in seen:
            unique.append(cid)
            seen.add(cid)
    return tuple(unique)


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
    creator_ids: tuple[int, ...]

    def is_creator(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.creator_ids

    @classmethod
    def load(cls) -> 'Settings':
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(dotenv_path=project_root / '.env')
        assets_raw = os.getenv('EXTERNAL_ASSETS_DIR', '').strip()
        assets_path = Path(assets_raw).expanduser().resolve() if assets_raw else None

        return cls(
            discord_token=os.getenv('DISCORD_TOKEN', '').strip(),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY', '').strip(),
            openrouter_model=os.getenv('OPENROUTER_MODEL', 'openrouter/free').strip(),
            external_assets_dir=assets_path,
            internal_assets_dir=project_root / 'bot_ui',
            default_mode=os.getenv('DEFAULT_MODE', 'normal').strip().lower(),
            log_level=os.getenv('LOG_LEVEL', 'INFO').strip().upper(),
            enable_mention_reply=os.getenv('ENABLE_MENTION_REPLY', 'true').strip().lower() in {'1', 'true', 'yes', 'on'},
            creator_ids=_parse_creator_ids(),
        )
