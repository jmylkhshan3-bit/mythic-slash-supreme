# Mythic Slash Supreme — Vision + AFK + YouTube Audio Build

Discord AI bot with:
- slash dashboard and restored mention replies
- OpenRouter free router for AI chat
- stronger image analysis for screenshots, UI, photos, and multi-image prompts
- AFK voice mode so the bot can sit silently inside a voice channel
- direct YouTube audio playback from URL or raw video ID

## Main commands
- `/ask`
- `/vision`
- `/setup`
- `/panel`
- `/status`
- `/voice_afk`
- `/voice_join`
- `/voice_leave`
- `/music`
- `/music_skip`
- `/music_stop`
- `/music_loop`
- `/gallery`
- `/vision_tips`

## Mention flow
Mention the bot in a server or send a DM. Attach images, text files, logs, code files, or zip files if needed.

## Voice flow
1. Join a voice channel.
2. Use `/voice_join` for live playback or `/voice_afk` for silent presence.
3. Use `/music` with a YouTube URL or raw video ID.

## Music notes
- This build uses `yt-dlp` + `ffmpeg`
- YouTube may sometimes require cookies on cloud hosts
- If YouTube blocks extraction, set:
  - `YTDLP_COOKIES_B64`
  - `YTDLP_USER_AGENT`

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token and OpenRouter key
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Railway notes
- Start command: `python main.py`
- `nixpacks.toml` already installs `ffmpeg`
- Enable Message Content Intent in Discord Developer Portal if you want mention replies
- Voice and music need Connect + Speak permission in the target voice channel

## Important
- YouTube playback is best-effort. Some videos may require cookies because of YouTube anti-bot checks.
- AI replies now ignore the Nvidia provider inside OpenRouter routing to reduce provider-side 404s.
