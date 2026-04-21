from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

DEFAULT_GUILD_STATE = {
    'mode': 'normal',
    'mention_enabled': True,
    'allowed_channel_ids': [],
    'system_note': '',
}


class GuildStateManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        if not self.path.exists():
            self.path.write_text('{}', encoding='utf-8')

    def _read_all(self) -> dict[str, dict]:
        try:
            return json.loads(self.path.read_text(encoding='utf-8') or '{}')
        except json.JSONDecodeError:
            return {}

    def _write_all(self, data: dict[str, dict]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def get(self, guild_id: int | None) -> dict:
        if guild_id is None:
            return DEFAULT_GUILD_STATE.copy()
        with self._lock:
            data = self._read_all()
            state = data.get(str(guild_id), {}).copy()
        merged = DEFAULT_GUILD_STATE.copy()
        merged.update(state)
        return merged

    def _update(self, guild_id: int, **patch) -> dict:
        with self._lock:
            data = self._read_all()
            key = str(guild_id)
            current = DEFAULT_GUILD_STATE.copy()
            current.update(data.get(key, {}))
            current.update(patch)
            data[key] = current
            self._write_all(data)
            return current.copy()

    def set_mode(self, guild_id: int, mode: str) -> dict:
        return self._update(guild_id, mode=mode)

    def toggle_mention(self, guild_id: int) -> dict:
        state = self.get(guild_id)
        return self._update(guild_id, mention_enabled=not state.get('mention_enabled', True))

    def toggle_channel_lock(self, guild_id: int, channel_id: int) -> dict:
        state = self.get(guild_id)
        channels = list(state.get('allowed_channel_ids', []))
        if channel_id in channels:
            channels.remove(channel_id)
        else:
            channels.append(channel_id)
        return self._update(guild_id, allowed_channel_ids=channels)

    def clear_channel_locks(self, guild_id: int) -> dict:
        return self._update(guild_id, allowed_channel_ids=[])

    def set_system_note(self, guild_id: int, note: str) -> dict:
        return self._update(guild_id, system_note=note.strip())
