# Mythic Slash Supreme

A Python Discord bot focused on:
- mention-to-reply AI
- slash commands
- premium embeds, views, modals, selectors, and animated processing states
- OpenRouter free router for chat
- AssemblyAI for speech-to-text
- free text-to-speech playback in voice channels
- official bot voice runtime design for wake-word workflows
- bundled branding assets from `bot_ui/`

## Main slash commands
- `/ask`
- `/setup`
- `/panel`
- `/info`
- `/help`
- `/status`
- `/mode`
- `/systemnote`
- `/profile`
- `/scene`
- `/settings`
- `/voice_action`
- `/voice_arm`
- `/voice_disarm`
- `/voice_status`
- `/voice_design`
- `/transcribe`

## Message flow
- Mention the bot in a server and start the request with `hey m`
- Or send a direct message
- Audio and text attachments can be analyzed along with your prompt

## Official voice runtime
- the project is designed around a bot account inside the voice channel
- `/voice_action action:join` joins your current voice channel
- `/voice_arm` stores and arms the wake-word profile for that server
- the voice profile can be edited from the Voice Hub modal
- `/voice_action action:speak text:...` speaks text in voice
- `/voice_disarm` disables the wake-word runtime
- `/voice_status` shows connection, armed state, wake phrase, and silence settings

## Railway
- Start command: `python main.py`
- `nixpacks.toml` installs `ffmpeg`
- Enable **Message Content Intent** if you want mention replies
- Add your secrets in Railway Variables instead of committing `.env`

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token, OpenRouter key, and AssemblyAI key
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Notes
- OpenRouter is configured for `openrouter/free`
- Chat requests are sent as a single `user` message for better compatibility with free routed models
- `discord-ext-voice-recv` is included as the optional live receive backend
- Do not commit `.env`, `.git`, or `__pycache__` into release zips
