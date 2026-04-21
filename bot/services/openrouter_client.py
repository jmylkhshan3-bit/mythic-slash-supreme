from __future__ import annotations

import aiohttp


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
        attachment_context: str = '',
        image_urls: list[str] | None = None,
        preferred_reply_language: str | None = None,
    ) -> str:
        guild_label = guild_name or 'Direct Chat'
        instruction = (
            'You are Mythic Slash Supreme, a Discord AI assistant. '
            'Be highly useful, polished, accurate, and readable. '
            f'Context: user={user_name}; location={guild_label}. '
            f'Server note: {system_note or "No extra server note."} '
            'Use markdown lightly and keep the answer clean. '
        )
        language = (preferred_reply_language or '').lower().strip()
        if language.startswith('ar'):
            instruction += 'Reply in Arabic unless the user clearly asks for another language. '
        elif language.startswith('en'):
            instruction += 'Reply in English. '
        else:
            instruction += 'If the user writes in Arabic, answer in Arabic first; otherwise answer in English. '
        if attachment_context:
            instruction += f"Attachment context follows. Use it directly.\n\n{attachment_context[:12000]}\n\n"
        user_text = instruction + 'User request:\n' + prompt

        content: list[dict[str, object]] | str
        if image_urls:
            content = [{'type': 'text', 'text': user_text}]
            for url in image_urls[:3]:
                content.append({'type': 'image_url', 'image_url': {'url': url}})
        else:
            content = user_text

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': 'https://openrouter.ai',
            'X-Title': 'Mythic Slash Supreme',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': content},
            ],
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as session:
            async with session.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload) as response:
                text = await response.text()
                if response.status >= 400:
                    raise RuntimeError(f'OpenRouter error {response.status}: {text[:500]}')
                data = await response.json()
        try:
            return data['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f'Unexpected OpenRouter response: {data}') from exc
