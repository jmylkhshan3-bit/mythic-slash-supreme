from __future__ import annotations

import re
import tempfile
from pathlib import Path

import aiohttp
import edge_tts

_ARABIC_RE = re.compile(r'[؀-ۿ]')


class TTSService:
    def __init__(
        self,
        *,
        voice_ar: str,
        voice_en: str,
        provider: str = 'kokoro',
        api_key: str = '',
        api_base: str = '',
        api_model: str = 'model_q8f16',
        api_voice: str = 'af_heart',
    ) -> None:
        self.voice_ar = voice_ar
        self.voice_en = voice_en
        self.provider = provider.strip().lower() or 'kokoro'
        self.api_key = api_key.strip()
        self.api_base = api_base.rstrip('/')
        self.api_model = api_model.strip() or 'model_q8f16'
        self.api_voice = api_voice.strip() or 'af_heart'

    def pick_voice(self, text: str, preferred: str | None = None) -> str:
        if self.provider in {'kokoro', 'openai_compatible'}:
            return self.api_voice
        if preferred == 'ar':
            return self.voice_ar
        if preferred == 'en':
            return self.voice_en
        return self.voice_ar if _ARABIC_RE.search(text or '') else self.voice_en

    async def synthesize(self, text: str, *, preferred: str | None = None) -> Path:
        if self.provider in {'kokoro', 'openai_compatible'} and self.api_base:
            return await self._synthesize_openai_compatible(text, preferred=preferred)
        return await self._synthesize_edge(text, preferred=preferred)

    async def _synthesize_edge(self, text: str, *, preferred: str | None = None) -> Path:
        voice = self.pick_voice(text, preferred=preferred)
        fd, tmp_path = tempfile.mkstemp(prefix='mythic_tts_', suffix='.mp3')
        Path(tmp_path).unlink(missing_ok=True)
        await edge_tts.Communicate(text, voice=voice).save(tmp_path)
        return Path(tmp_path)

    async def _synthesize_openai_compatible(self, text: str, *, preferred: str | None = None) -> Path:
        voice = self.pick_voice(text, preferred=preferred)
        fd, tmp_path = tempfile.mkstemp(prefix='mythic_tts_api_', suffix='.mp3')
        Path(tmp_path).unlink(missing_ok=True)
        timeout = aiohttp.ClientTimeout(total=120)
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        payload = {'model': self.api_model, 'voice': voice, 'input': text, 'format': 'mp3'}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f'{self.api_base}/audio/speech', headers=headers, json=payload) as response:
                body = await response.read()
                if response.status >= 400:
                    raise RuntimeError(f'TTS API failed {response.status}: {body[:500].decode("utf-8", errors="ignore")}')
        Path(tmp_path).write_bytes(body)
        return Path(tmp_path)
