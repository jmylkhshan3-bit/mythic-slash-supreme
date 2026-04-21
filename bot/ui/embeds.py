from __future__ import annotations

from datetime import datetime, timezone

import discord

from bot.constants import BOT_VERSION, MODE_PRESETS


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


def apply_branding(embed: discord.Embed, *, has_banner: bool, has_avatar: bool) -> discord.Embed:
    if has_banner:
        embed.set_image(url='attachment://bot_banner_680x240.png')
    if has_avatar:
        embed.set_thumbnail(url='attachment://bot_avatar_1024.png')
    return embed


def shell(title: str, description: str, mode: str) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = discord.Embed(
        title=f'{preset.emoji} {title}',
        description=description,
        color=preset.color,
    )
    embed.set_footer(text=f'Mythic Slash Supreme • {preset.label} • {now_stamp()}')
    return embed


def loading_embed(mode: str, line: str, prompt: str, user_name: str) -> discord.Embed:
    embed = shell('Response Engine', line, mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.add_field(name='User', value=user_name[:256], inline=True)
    return embed


def response_embed(mode: str, prompt: str, answer: str, user_name: str) -> discord.Embed:
    embed = shell('AI Reply', answer[:4000], mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.add_field(name='Requested by', value=user_name[:256], inline=True)
    return embed


def panel_embed(snapshot: dict, mode: str, activation_phrase: str, music_state: dict) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = shell('Command Center', 'Legendary setup surface for AI, voice capture, image analysis, and YouTube music.', mode)
    embed.add_field(name='Current Mode', value=f'{preset.emoji} {preset.label}', inline=True)
    embed.add_field(name='Mentions', value='Enabled' if snapshot.get('mention_enabled') else 'Disabled', inline=True)
    embed.add_field(name='Channel Locks', value=str(len(snapshot.get('allowed_channel_ids', []))), inline=True)
    embed.add_field(
        name='AI Surface',
        value=(
            '• Slash asks with attachments\n'
            '• Mention replies restored\n'
            '• DM support\n'
            '• Image-aware prompts\n'
            '• Voice asks after wake phrase'
        ),
        inline=False,
    )
    embed.add_field(
        name='Voice Surface',
        value=(
            f'• Wake phrase: `{activation_phrase}`\n'
            f'• Input language: `{snapshot.get("voice_input_language", "auto")}`\n'
            f'• Reply language: `{snapshot.get("voice_output_language", "auto")}`\n'
            f'• Silence window: `{snapshot.get("voice_silence_seconds", 5.0)}` sec\n'
            '• STT + TTS via ElevenLabs\n'
            '• `/speak` auto-joins your voice room'
        ),
        inline=False,
    )
    music_text = 'Inactive'
    if music_state.get('active'):
        music_text = f'Playing **{music_state.get("title", "YouTube audio")}**'
    embed.add_field(
        name='Music Surface',
        value=(
            f'{music_text}\n'
            f'Loop: `{"on" if music_state.get("loop") else "off"}`\n'
            'Use `/music`, `/loop_music`, `/end_music`'
        ),
        inline=False,
    )
    return embed


def status_embed(snapshot: dict, mode: str, asset_status: dict[str, str], model_name: str, music_state: dict) -> discord.Embed:
    channels = snapshot.get('allowed_channel_ids', [])
    embed = shell('Status Wall', 'Runtime snapshot, voice profile, music state, and asset health.', mode)
    embed.add_field(name='Mode', value=snapshot.get('mode', 'normal'), inline=True)
    embed.add_field(name='Mention Replies', value='ON' if snapshot.get('mention_enabled') else 'OFF', inline=True)
    embed.add_field(name='Allowed Channels', value=str(len(channels)), inline=True)
    embed.add_field(name='Model', value=model_name, inline=False)
    embed.add_field(
        name='Voice Profile',
        value=(
            f'Wake: `{snapshot.get("voice_wake_phrase", "hey m")}`\n'
            f'Input: `{snapshot.get("voice_input_language", "auto")}`\n'
            f'Reply: `{snapshot.get("voice_output_language", "auto")}`\n'
            f'Silence: `{snapshot.get("voice_silence_seconds", 5.0)}` sec\n'
            f'Trigger: `{snapshot.get("voice_trigger_level_db", -55.0)} dB`\n'
            'Reply language: `auto Arabic / English`'
        ),
        inline=False,
    )
    embed.add_field(
        name='Music',
        value=(
            f'Active: `{"yes" if music_state.get("active") else "no"}`\n'
            f'Loop: `{"on" if music_state.get("loop") else "off"}`\n'
            f'Title: `{music_state.get("title") or "none"}`'
        ),
        inline=False,
    )
    embed.add_field(
        name='Assets',
        value=(
            f"Source: `{asset_status['source']}`\n"
            f"Root: `{asset_status['root']}`\n"
            f"Avatar: `{asset_status['avatar']}`\n"
            f"Banner: `{asset_status['banner']}`\n"
            f"Icons: `{asset_status['icons']}`"
        ),
        inline=False,
    )
    note = snapshot.get('system_note') or 'No server note has been set yet.'
    embed.add_field(name='Server Note', value=note[:1024], inline=False)
    return embed


def info_embed(mode: str, model_name: str, icon_count: int) -> discord.Embed:
    embed = shell('Build Profile', 'Mythic is tuned for premium slash UX, bilingual voice replies, file analysis, and YouTube playback.', mode)
    embed.add_field(name='AI Router', value=model_name, inline=False)
    embed.add_field(name='Voice', value='ElevenLabs STT + TTS with auto Arabic/English reply flow', inline=False)
    embed.add_field(name='Icons Loaded', value=str(icon_count), inline=True)
    embed.add_field(name='Version', value=BOT_VERSION, inline=True)
    return embed


def help_embed(mode: str) -> discord.Embed:
    embed = shell('Slash Command Deck', 'Every control is slash-based. Mention replies and DMs are available too.', mode)
    embed.add_field(name='/ask', value='Ask the AI with optional attachment or image context.', inline=True)
    embed.add_field(name='/setup', value='Open the main control dashboard.', inline=True)
    embed.add_field(name='/panel', value='Open the dashboard again.', inline=True)
    embed.add_field(name='/status', value='Inspect runtime state and asset health.', inline=True)
    embed.add_field(name='/speak', value='Join your voice channel and speak text aloud.', inline=True)
    embed.add_field(name='/music', value='Play a YouTube link in voice.', inline=True)
    embed.add_field(name='/loop_music', value='Toggle looping for the YouTube track.', inline=True)
    embed.add_field(name='/end_music', value='Stop the active track.', inline=True)
    embed.add_field(name='/transcribe', value='Transcribe an attached audio or video file.', inline=True)
    embed.add_field(name='/gallery', value='See the asset gallery and icon catalog.', inline=True)
    return embed


def gallery_embed(mode: str, icon_names: list[str]) -> discord.Embed:
    listed = '\n'.join(f'• `{name}`' for name in icon_names[:30]) or 'No icons found.'
    embed = shell('Asset Gallery', 'Bundled visuals that back the command center and brand surface.', mode)
    embed.add_field(name='Icon Catalog', value=listed[:1024], inline=False)
    embed.add_field(name='Brand Surface', value='Avatar + banner are bundled inside `bot_ui/brand/`.', inline=False)
    return embed


def transcript_embed(mode: str, source_name: str, transcript: str, language_code: str | None) -> discord.Embed:
    embed = shell('Transcript', transcript[:4000] or '[empty transcript]', mode)
    embed.add_field(name='Source', value=source_name, inline=True)
    embed.add_field(name='Language', value=language_code or 'auto', inline=True)
    return embed
