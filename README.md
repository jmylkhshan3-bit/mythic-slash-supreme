# Mythic Slash Supreme

Discord AI bot with slash commands, mention replies, bundled assets, OpenRouter, and an official-bot voice runtime.

## Main commands
- `/ask`
- `/setup`
- `/panel`
- `/status`
- `/voice_join`
- `/voice_leave`
- `/speak`
- `/voice_action`
- `/voice_arm`
- `/voice_disarm`
- `/voice_status`
- `/transcribe`

## Voice flow
1. Join a voice channel.
2. Run `/voice_join`.
3. Run `/voice_arm`.
4. Say the wake phrase (default: `hey m`) and your request.
5. The bot records until silence, transcribes with AssemblyAI, asks OpenRouter, then speaks back.

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token, OpenRouter key, and AssemblyAI key
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Railway notes
- Start command: `python main.py`
- `nixpacks.toml` installs `ffmpeg`
- `imageio-ffmpeg` is also bundled as a fallback
- If you want mention replies, enable Message Content Intent in Discord Developer Portal

## TTS options
- Default: `TTS_PROVIDER=edge` (no key required)
- Optional: set `TTS_PROVIDER=openai_compatible` and provide `TTS_API_KEY` + `TTS_API_BASE`
