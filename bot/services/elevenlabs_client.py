from __future__ import annotations

import aiohttp
from dataclasses import dataclass


@dataclass(slots=True)
class TranscriptResult:
    text: str
    language_code: str | None


class ElevenLabsClient:
    def __init__(
        self,
        api_key: str,
        tts_voice_id: str,
        tts_model_id: str,
        stt_model_id: str,
        en_voice_id: str | None = None,
        ar_voice_id: str | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.tts_voice_id = tts_voice_id.strip()
        self.en_voice_id = (en_voice_id or tts_voice_id).strip()
        self.ar_voice_id = (ar_voice_id or tts_voice_id).strip()
        self.tts_model_id = tts_model_id.strip() or 'eleven_flash_v2_5'
        self.stt_model_id = stt_model_id.strip() or 'scribe_v2'
        self.base_url = 'https://api.elevenlabs.io/v1'

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def headers(self) -> dict[str, str]:
        return {'xi-api-key': self.api_key}

    def pick_voice_id(self, preferred_language: str | None = None) -> str:
        language = (preferred_language or '').lower().strip()
        if language.startswith('ar'):
            return self.ar_voice_id or self.tts_voice_id
        if language.startswith('en'):
            return self.en_voice_id or self.tts_voice_id
        return self.tts_voice_id

    async def text_to_speech(self, *, text: str, preferred_language: str | None = None) -> bytes:
        if not self.enabled:
            raise RuntimeError('ELEVENLABS_API_KEY is missing.')
        voice_id = self.pick_voice_id(preferred_language)
        url = f'{self.base_url}/text-to-speech/{voice_id}?output_format=mp3_44100_128'
        payload = {
            'text': text,
            'model_id': self.tts_model_id,
        }
        timeout = aiohttp.ClientTimeout(total=120)
        headers = {**self.headers(), 'Content-Type': 'application/json'}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                body = await response.read()
                if response.status >= 400:
                    raise RuntimeError(f'ElevenLabs TTS failed {response.status}: {body[:500].decode("utf-8", errors="ignore")}')
                return body

    async def speech_to_text(self, *, data: bytes, filename: str = 'audio.wav', language_code: str | None = None) -> TranscriptResult:
        if not self.enabled:
            raise RuntimeError('ELEVENLABS_API_KEY is missing.')
        form = aiohttp.FormData()
        form.add_field('model_id', self.stt_model_id)
        if language_code and language_code not in {'auto', ''}:
            form.add_field('language_code', language_code)
        form.add_field('file', data, filename=filename, content_type='audio/wav')
        timeout = aiohttp.ClientTimeout(total=180)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f'{self.base_url}/speech-to-text', headers=self.headers(), data=form) as response:
                text = await response.text()
                if response.status >= 400:
                    raise RuntimeError(f'ElevenLabs STT failed {response.status}: {text[:500]}')
                payload = await response.json()
        return TranscriptResult(
            text=(payload.get('text') or '').strip(),
            language_code=payload.get('language_code'),
        )
