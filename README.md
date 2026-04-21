# Mythic Slash Supreme — Vision + AFK Build

Discord AI bot with:
- slash dashboard and restored mention replies
- OpenRouter free router for AI chat
- stronger image analysis for screenshots, UI, photos, and multi-image prompts
- AFK voice mode so the bot can sit silently inside a voice channel
- bundled internal assets for Railway and mobile

## Main commands
- `/ask`
- `/vision`
- `/setup`
- `/panel`
- `/status`
- `/voice_afk`
- `/voice_join`
- `/voice_leave`
- `/gallery`
- `/vision_tips`

## Mention flow
Mention the bot in a server or send a DM. Attach images, text files, logs, code files, or zip files if needed.

## Voice flow
1. Join a voice channel.
2. Use `/voice_afk` or `/voice_join`.
3. The bot joins silently and tries to self-mute/self-deafen.
4. Use `/voice_leave` when you want it to leave.

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token and OpenRouter key
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Railway notes
- Start command: `python main.py`
- If you want mention replies, enable Message Content Intent in Discord Developer Portal
- Voice AFK mode needs Connect permission in the target voice channel

## Important
- This build removes live call, speech playback, speech-to-text, and music.
- Image analysis is richer than before, especially for screenshots and UI troubleshooting.
