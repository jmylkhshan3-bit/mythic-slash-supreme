# Mythic Slash Supreme — Creator Build

Discord AI bot with:
- slash dashboard and restored mention replies
- OpenRouter free router for AI chat
- stronger image analysis for screenshots, UI, photos, and multi-image prompts
- AFK voice mode so the bot can sit silently inside a voice channel
- direct YouTube audio playback from URL or raw video ID
- creator recognition by Discord ID with elevated respect and creator-only bypass for mention/channel restrictions

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
- `/creator`
- `/gallery`
- `/vision_tips`

## Creator mode
Set your Discord ID in:
- `CREATOR_IDS`
- or `CREATOR_ID`

When the creator talks to the bot:
- the bot recognizes them by Discord ID
- replies with elevated respect such as "my creator"
- bypasses mention disable and channel lock checks
- prioritizes creator requests within what Discord and the APIs can actually do

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token and OpenRouter key
3. Put your Discord user ID in `CREATOR_IDS`
4. Install deps: `pip install -r requirements.txt`
5. Run: `python main.py`

## Railway notes
- Start command: `python main.py`
- `nixpacks.toml` already installs `ffmpeg`
- Enable Message Content Intent in Discord Developer Portal if you want mention replies
- Voice and music need Connect + Speak permission in the target voice channel

## Music notes
- This build uses `yt-dlp` + `ffmpeg`
- YouTube may sometimes require cookies on cloud hosts
- If YouTube blocks extraction, set:
  - `YTDLP_COOKIES_B64`
  - `YTDLP_USER_AGENT`
