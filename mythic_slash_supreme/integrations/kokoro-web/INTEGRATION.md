# Kokoro Web integration for Mythic Slash Supreme

This bot expects Kokoro Web to be running separately and reachable at `/api/v1`.

## Recommended env
```env
TTS_PROVIDER=kokoro
TTS_API_BASE=https://your-kokoro-host/api/v1
TTS_API_KEY=your-kokoro-api-key
TTS_API_MODEL=model_q8f16
TTS_API_VOICE=af_heart
```

## Minimal Docker example
```yaml
services:
  kokoro-web:
    image: ghcr.io/eduardolat/kokoro-web:latest
    ports:
      - "3000:3000"
    environment:
      - KW_SECRET_API_KEY=your-api-key
    restart: unless-stopped
```
