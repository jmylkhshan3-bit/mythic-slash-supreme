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
- If YouTube blocks extraction, set one of these:
  - `YTDLP_COOKIES_B64`
  - `YTDLP_COOKIES_B64_FILE`
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

- If Railway still cannot find ffmpeg, add `RAILPACK_DEPLOY_APT_PACKAGES=ffmpeg` and `FFMPEG_PATH=ffmpeg` in Variables.



## Long base64 cookie workaround
If the base64 cookie text is too long for Railway variables, save it as a file inside the project, for example:

```text
data/cookies/cookies_base64.txt
```

Then set:

```env
YTDLP_COOKIES_B64_FILE=/app/data/cookies/cookies_base64.txt
YTDLP_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36
```

The bot will read the base64 text from that file, decode it at runtime, and pass the resulting cookies to `yt-dlp`.


## Creator mode
You can register one or more Discord user IDs as the project creator:

```env
CREATOR_IDS=123456789012345678,987654321098765432
CREATOR_TITLE=the Supreme Creator
```

Or use a single ID:

```env
CREATOR_ID=123456789012345678
```

When the creator talks to the bot:
- creator recognition becomes active
- creator phrasing becomes more respectful
- creator mention replies bypass channel locks and mention toggles
- the bot avoids moralizing or lecturing the creator's tone
