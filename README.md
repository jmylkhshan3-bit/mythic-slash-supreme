# Mythic Slash Supreme Reworked

Discord AI bot with:
- slash dashboard and restored mention replies
- OpenRouter free router for AI chat
- ElevenLabs text-to-speech and speech-to-text
- wake phrase voice capture (`hey m`) when the bot is in a voice channel
- automatic Arabic / English voice replies
- YouTube music playback with loop support
- bundled internal assets for Railway and mobile

## Main commands
- `/ask`
- `/setup`
- `/panel`
- `/status`
- `/speak`
- `/music`
- `/loop_music`
- `/end_music`
- `/gallery`
- `/transcribe`

## Mention flow
Mention the bot in a server or send a DM. Attach images, text files, audio, video, or zip files if needed.

## Voice flow
1. Join a voice channel.
2. Use `/speak` once or `/music` once so the bot joins your voice room.
3. Say `hey m` followed by your request.
4. After about 5 seconds of silence, the bot transcribes the audio, asks the AI, and speaks the answer in Arabic or English automatically.

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token, OpenRouter key, and ElevenLabs key
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Railway notes
- Start command: `python main.py`
- `nixpacks.toml` installs `ffmpeg`
- `imageio-ffmpeg` is bundled as a fallback
- If you want mention replies, enable Message Content Intent in Discord Developer Portal
