from __future__ import annotations

import asyncio
from dataclasses import dataclass

import aiohttp


@dataclass(slots=True)
class TranscriptResult:
    text: str
    utterances: list[dict]
    audio_duration: int | None
    language_code: str | None


class AssemblyAIClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        self.base_url = 'https://api.assemblyai.com'

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {'Authorization': self.api_key}

    async def transcribe_bytes(
        self,
        *,
        data: bytes,
        speaker_labels: bool = False,
        language_detection: bool = True,
        language_code: str | None = None,
        expected_languages: list[str] | None = None,
        timeout_seconds: int = 180,
    ) -> TranscriptResult:
        if not self.enabled:
            raise RuntimeError('ASSEMBLYAI_API_KEY is missing.')
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f'{self.base_url}/v2/upload',
                headers=self._headers(),
                data=data,
            ) as upload_response:
                upload_text = await upload_response.text()
                if upload_response.status >= 400:
                    raise RuntimeError(f'AssemblyAI upload failed {upload_response.status}: {upload_text[:500]}')
                upload_json = await upload_response.json()
            transcript_payload: dict[str, object] = {
                'audio_url': upload_json['upload_url'],
                'speaker_labels': speaker_labels,
            }
            if language_code:
                transcript_payload['language_code'] = language_code
                transcript_payload['language_detection'] = False
            else:
                transcript_payload['language_detection'] = language_detection
                if language_detection and expected_languages:
                    transcript_payload['language_detection_options'] = {
                        'expected_languages': expected_languages,
                        'fallback_language': 'auto',
                    }
            async with session.post(
                f'{self.base_url}/v2/transcript',
                headers={**self._headers(), 'Content-Type': 'application/json'},
                json=transcript_payload,
            ) as transcript_response:
                transcript_text = await transcript_response.text()
                if transcript_response.status >= 400:
                    raise RuntimeError(f'AssemblyAI transcript start failed {transcript_response.status}: {transcript_text[:500]}')
                transcript_json = await transcript_response.json()
            transcript_id = transcript_json['id']
            for _ in range(max(20, timeout_seconds // 2)):
                await asyncio.sleep(2)
                async with session.get(
                    f'{self.base_url}/v2/transcript/{transcript_id}',
                    headers=self._headers(),
                ) as poll_response:
                    poll_text = await poll_response.text()
                    if poll_response.status >= 400:
                        raise RuntimeError(f'AssemblyAI transcript poll failed {poll_response.status}: {poll_text[:500]}')
                    poll_json = await poll_response.json()
                status = poll_json.get('status')
                if status == 'completed':
                    return TranscriptResult(
                        text=(poll_json.get('text') or '').strip(),
                        utterances=poll_json.get('utterances') or [],
                        audio_duration=poll_json.get('audio_duration'),
                        language_code=poll_json.get('language_code'),
                    )
                if status == 'error':
                    raise RuntimeError(f"AssemblyAI error: {poll_json.get('error', 'unknown error')}")
            raise RuntimeError('AssemblyAI transcription timed out.')
