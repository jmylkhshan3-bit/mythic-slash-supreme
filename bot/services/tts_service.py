from __future__ import annotations

import tempfile
from pathlib import Path

from bot.services.elevenlabs_client import ElevenLabsClient


class TTSService:
    def __init__(self, *, elevenlabs_client: ElevenLabsClient) -> None:
        self.client = elevenlabs_client

    async def synthesize(self, text: str, *, preferred: str | None = None) -> Path:
        audio = await self.client.text_to_speech(text=text, preferred_language=preferred)
        fd, tmp_path = tempfile.mkstemp(prefix='mythic_tts_', suffix='.mp3')
        path = Path(tmp_path)
        path.write_bytes(audio)
        if path.stat().st_size <= 512:
            raise RuntimeError('ElevenLabs returned an empty or invalid audio file.')
        return path
