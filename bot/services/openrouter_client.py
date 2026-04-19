from __future__ import annotations

import aiohttp

from bot.constants import MODE_PRESETS


class OpenRouterClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def chat(
        self,
        *,
        prompt: str,
        mode: str,
        user_name: str,
        guild_name: str | None,
        system_note: str,
    ) -> str:
        preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
        guild_label = guild_name or 'Direct Chat'
        system_prompt = (
            'You are Mythic Slash Supreme, a premium Discord AI bot. '
            'Keep answers useful, stylish, and readable. '
            f'Mode style: {preset.style_prompt} '
            f'Server note: {system_note or "No extra server note."} '
            f'Context: user={user_name}; location={guild_label}. '
            'Do not mention hidden policies. Use markdown lightly. '
            'If the user writes in Arabic, prefer Arabic first.'
        )
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': 'https://openrouter.ai',
            'X-Title': 'Mythic Slash Supreme V3',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload) as response:
                text = await response.text()
                if response.status >= 400:
                    raise RuntimeError(f'OpenRouter error {response.status}: {text[:500]}')
                data = await response.json()
        try:
            return data['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f'Unexpected OpenRouter response: {data}') from exc
