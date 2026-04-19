from __future__ import annotations

from pathlib import Path

import discord


class AssetManager:
    def __init__(self, internal_root: Path, external_root: Path | None = None) -> None:
        self.internal_root = internal_root
        self.external_root = external_root

    def _roots(self) -> list[Path]:
        roots: list[Path] = []
        if self.external_root:
            roots.append(self.external_root)
        roots.append(self.internal_root)
        return roots

    def _candidate_paths(self, root: Path, kind: str) -> list[Path]:
        if kind == 'avatar':
            return [
                root / 'brand' / 'bot_avatar_1024.png',
                root / 'bot_ui' / 'brand' / 'bot_avatar_1024.png',
            ]
        if kind == 'banner':
            return [
                root / 'brand' / 'bot_banner_680x240.png',
                root / 'bot_ui' / 'brand' / 'bot_banner_680x240.png',
            ]
        return []

    def _find_file(self, kind: str) -> Path | None:
        for root in self._roots():
            for path in self._candidate_paths(root, kind):
                if path.exists():
                    return path
        return None

    def avatar_path(self) -> Path | None:
        return self._find_file('avatar')

    def banner_path(self) -> Path | None:
        return self._find_file('banner')

    def avatar_file(self) -> discord.File | None:
        path = self.avatar_path()
        return discord.File(path, filename='bot_avatar_1024.png') if path else None

    def banner_file(self) -> discord.File | None:
        path = self.banner_path()
        return discord.File(path, filename='bot_banner_680x240.png') if path else None

    def icon_names(self) -> list[str]:
        names: set[str] = set()
        for root in self._roots():
            for icon_dir in (root / 'icons', root / 'svg' / 'icons', root / 'bot_ui' / 'icons'):
                if icon_dir.exists():
                    names.update(p.name for p in icon_dir.glob('*.svg'))
        return sorted(names)

    def asset_status(self) -> dict[str, str]:
        active_root = self.external_root if self.external_root and self.external_root.exists() else self.internal_root
        return {
            'root': str(active_root),
            'avatar': 'found' if self.avatar_path() else 'missing',
            'banner': 'found' if self.banner_path() else 'missing',
            'icons': f'{len(self.icon_names())} file(s)',
            'source': 'external + internal fallback' if self.external_root else 'internal bundled bot_ui assets',
        }
