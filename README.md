# Mythic Slash Supreme V3

Discord AI bot with:
- slash-first controls
- mention-to-reply AI
- richer UI (buttons, selects, modals, dashboards)
- enhanced loading animation and status rotation
- internal bundled assets for Railway and mobile
- OpenRouter support via `google/gemma-3-4b-it:free`

## Main commands
- `/ask`
- `/setup`
- `/panel`
- `/mode`
- `/status`
- `/info`
- `/help`
- `/profile`
- `/scene`
- `/ping`
- `/about`
- `/locks`
- `/settings`
- `/systemnote`

## Quick start
1. Copy `.env.example` to `.env`
2. Fill your Discord token and OpenRouter key
3. Install deps: `pip install -r requirements.txt`
4. Run: `python main.py`

## Railway notes
- Assets are already bundled inside `bot_ui/`
- Start command: `python main.py`
- If you want mention replies, enable `Message Content Intent` in Discord Developer Portal
- If you only want slash commands, set `ENABLE_MENTION_REPLY=false`

## Important
If your token or API key was ever shared publicly, rotate it before using this project.


## Project layout
```
mythic_slash_supreme/
├── bot/
├── bot_ui/
│   ├── brand/
│   └── icons/
├── main.py
└── requirements.txt
```
