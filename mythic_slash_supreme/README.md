# Mythic Slash Supreme Ultimate

Discord AI bot with slash commands, voice runtime, image-aware analysis, Kokoro TTS integration, and music playback.

## Included systems
- OpenRouter free router for AI replies
- AssemblyAI for speech-to-text
- Kokoro Web integration (OpenAI-compatible TTS)
- Discord voice receive runtime for wake phrase flows
- yt-dlp music playback for YouTube and Spotify-to-YouTube resolution
- Internal UI assets and icons

## Important
This repo includes a copy of `integrations/kokoro-web/` as the recommended TTS companion service. Run Kokoro first, then point `TTS_API_BASE` at its `/api/v1` endpoint.

## Quick start
1. Copy `.env.example` to `.env`
2. Fill Discord, OpenRouter, AssemblyAI, and Kokoro values
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Railway
- Start command: `python main.py`
- This project includes `nixpacks.toml` for ffmpeg support
- Set `TTS_PROVIDER=kokoro`
- Set `TTS_API_BASE=https://your-kokoro-host/api/v1`

## Notes
- Voice receive is still an experimental Discord runtime
- Spotify links are resolved by extracting metadata and searching a matching playable source
- Image analysis uses multimodal requests when the selected free model supports images
