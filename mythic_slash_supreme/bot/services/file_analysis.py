from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

import discord

TEXT_SUFFIXES = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.csv', '.html', '.css', '.xml', '.yaml', '.yml', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.sql'}
AUDIO_SUFFIXES = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.mp4', '.mov', '.webm'}
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


class AttachmentAnalyzer:
    def __init__(self, stt_client) -> None:
        self.stt = stt_client

    async def analyze(self, attachments: list[discord.Attachment]) -> tuple[str, list[str]]:
        if not attachments:
            return '', []
        chunks: list[str] = []
        images: list[str] = []
        for attachment in attachments[:4]:
            suffix = Path(attachment.filename).suffix.lower()
            content_type = (attachment.content_type or '').lower()
            chunks.append(f'Attachment: {attachment.filename} ({content_type or "unknown"})')
            if suffix in TEXT_SUFFIXES or content_type.startswith('text/'):
                try:
                    raw = await attachment.read()
                    text = raw.decode('utf-8', errors='ignore')
                except Exception as exc:
                    text = f'Failed to read text attachment: {exc}'
                chunks.append(text[:6000])
                continue
            if suffix == '.zip':
                try:
                    raw = await attachment.read()
                    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                        names = zf.namelist()[:120]
                    chunks.append('ZIP entries:\n' + '\n'.join(names))
                except Exception as exc:
                    chunks.append(f'Failed to inspect ZIP: {exc}')
                continue
            if suffix in AUDIO_SUFFIXES or content_type.startswith('audio/') or content_type.startswith('video/'):
                if not self.stt.enabled:
                    chunks.append('Audio/video attachment detected, but ASSEMBLYAI_API_KEY is missing.')
                    continue
                try:
                    raw = await attachment.read()
                    result = await self.stt.transcribe_bytes(data=raw, speaker_labels=False, expected_languages=['ar', 'en'])
                    chunks.append('Transcription:\n' + (result.text or '[no speech detected]'))
                except Exception as exc:
                    chunks.append(f'Failed to transcribe audio: {exc}')
                continue
            if suffix in IMAGE_SUFFIXES or content_type.startswith('image/'):
                try:
                    raw = await attachment.read()
                    mime = content_type or 'image/png'
                    data_url = 'data:' + mime + ';base64,' + base64.b64encode(raw).decode('ascii')
                    images.append(data_url)
                    chunks.append('Image attached. Vision analysis is enabled for this request.')
                except Exception as exc:
                    chunks.append(f'Failed to load image: {exc}')
                continue
            chunks.append('Unsupported attachment type for deep parsing in this build.')
        return '\n\n'.join(chunks)[:12000], images
