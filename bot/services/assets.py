from __future__ import annotations

from pathlib import Path

import discord


class AssetManager:
    def __init__(self, internal_root: Path, external_root: Path | None) -> None:
        self.internal_root = internal_root
        self.external_root = external_root

    def _roots(self) -> list[tuple[str, Path]]:
        roots: list[tuple[str, Path]] = []
        if self.external_root and self.external_root.exists():
            roots.append(('external', self.external_root))
        if self.internal_root.exists():
            roots.append(('internal', self.internal_root))
        return roots

    def _find(self, *parts: str) -> tuple[str, Path] | None:
        for source, root in self._roots():
            path = root.joinpath(*parts)
            if path.exists():
                return source, path
        return None

    def avatar_path(self) -> Path | None:
        found = self._find('brand', 'bot_avatar_1024.png')
        return found[1] if found else None

    def banner_path(self) -> Path | None:
        found = self._find('brand', 'bot_banner_680x240.png')
        return found[1] if found else None

    def avatar_file(self) -> discord.File | None:
        path = self.avatar_path()
        return discord.File(path, filename='bot_avatar_1024.png') if path else None

    def banner_file(self) -> discord.File | None:
        path = self.banner_path()
        return discord.File(path, filename='bot_banner_680x240.png') if path else None

    def icon_names(self) -> list[str]:
        for _, root in self._roots():
            icon_dir = root / 'icons'
            if icon_dir.exists():
                return sorted(p.name for p in icon_dir.glob('*.svg'))
            alt_icon_dir = root / 'svg' / 'icons'
            if alt_icon_dir.exists():
                return sorted(p.name for p in alt_icon_dir.glob('*.svg'))
        return []

    def asset_status(self) -> dict[str, str]:
        source = 'missing'
        root = 'not set'
        if self.external_root and self.external_root.exists():
            source = 'external'
            root = str(self.external_root)
        elif self.internal_root.exists():
            source = 'internal'
            root = str(self.internal_root)
        return {
            'source': source,
            'root': root,
            'avatar': 'found' if self.avatar_path() else 'missing',
            'banner': 'found' if self.banner_path() else 'missing',
            'icons': f'{len(self.icon_names())} file(s)',
        }
