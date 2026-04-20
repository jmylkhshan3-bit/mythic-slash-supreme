from __future__ import annotations

import re
import tempfile
from pathlib import Path

import edge_tts


_ARABIC_RE = re.compile(r'[\u0600-\u06FF]')


class TTSService:
    def __init__(self, *, voice_ar: str, voice_en: str) -> None:
        self.voice_ar = voice_ar
        self.voice_en = voice_en

    def pick_voice(self, text: str, preferred: str | None = None) -> str:
        if preferred == 'ar':
            return self.voice_ar
        if preferred == 'en':
            return self.voice_en
        return self.voice_ar if _ARABIC_RE.search(text or '') else self.voice_en

    async def synthesize(self, text: str, *, preferred: str | None = None) -> Path:
        voice = self.pick_voice(text, preferred=preferred)
        fd, tmp_path = tempfile.mkstemp(prefix='mythic_tts_', suffix='.mp3')
        Path(tmp_path).unlink(missing_ok=True)
        await edge_tts.Communicate(text, voice=voice).save(tmp_path)
        return Path(tmp_path)
