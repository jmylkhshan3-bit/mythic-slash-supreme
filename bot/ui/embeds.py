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


def panel_embed(snapshot: dict, mode: str, voice_snapshot: dict[str, object]) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = shell('Command Center', 'Legendary setup surface for AI, image analysis, file parsing, mention replies, and silent AFK voice presence.', mode)
    embed.add_field(name='Current Mode', value=f'{preset.emoji} {preset.label}', inline=True)
    embed.add_field(name='Mentions', value='Enabled' if snapshot.get('mention_enabled') else 'Disabled', inline=True)
    embed.add_field(name='Channel Locks', value=str(len(snapshot.get('allowed_channel_ids', []))), inline=True)
    embed.add_field(
        name='Vision Surface',
        value=(
            '• Detailed image analysis with scene, objects, layout, OCR hints, and style clues\n'
            '• Better multi-image prompts\n'
            '• File-aware slash asks for text, code, ZIP indexes, and screenshots\n'
            '• Mention replies restored in channels and DMs'
        ),
        inline=False,
    )
    voice_line = f"Connected to `{voice_snapshot['channel_name']}`" if voice_snapshot.get('connected') else 'Not connected to any voice channel'
    embed.add_field(
        name='AFK Voice Surface',
        value=(
            f'• Status: {voice_line}\n'
            '• Join a voice room in silent AFK mode\n'
            '• Bot self-mutes and self-deafens when possible\n'
            '• No live call, no speech playback, no listening pipeline'
        ),
        inline=False,
    )
    embed.add_field(
        name='Main Commands',
        value='Use `/ask`, `/vision`, `/voice_afk`, `/voice_join`, `/voice_leave`, `/status`, `/gallery`.',
        inline=False,
    )
    return embed


def status_embed(snapshot: dict, mode: str, asset_status: dict[str, str], model_name: str, voice_snapshot: dict[str, object]) -> discord.Embed:
    channels = snapshot.get('allowed_channel_ids', [])
    embed = shell('Status Wall', 'Runtime snapshot, AFK voice state, and asset health.', mode)
    embed.add_field(name='Mode', value=snapshot.get('mode', 'normal'), inline=True)
    embed.add_field(name='Mention Replies', value='ON' if snapshot.get('mention_enabled') else 'OFF', inline=True)
    embed.add_field(name='Allowed Channels', value=str(len(channels)), inline=True)
    embed.add_field(name='Model', value=model_name, inline=False)
    voice_state = 'connected' if voice_snapshot.get('connected') else 'idle'
    embed.add_field(
        name='AFK Voice',
        value=(
            f'State: `{voice_state}`\n'
            f"Channel: `{voice_snapshot.get('channel_name') or 'none'}`\n"
            f"Style: `{voice_snapshot.get('afk_style', 'idle')}`"
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
    embed = shell('Build Profile', 'Mythic is tuned for premium slash UX, richer image analysis, restored mentions, and clean AFK voice support.', mode)
    embed.add_field(name='AI Router', value=model_name, inline=False)
    embed.add_field(name='Voice Mode', value='Silent AFK join only', inline=False)
    embed.add_field(name='Icons Loaded', value=str(icon_count), inline=True)
    embed.add_field(name='Version', value=BOT_VERSION, inline=True)
    return embed


def help_embed(mode: str) -> discord.Embed:
    embed = shell('Slash Command Deck', 'Every control is slash-based. Mention replies and DMs are available too.', mode)
    embed.add_field(name='/ask', value='Ask the AI with optional attachment or image context.', inline=True)
    embed.add_field(name='/vision', value='Analyze one to three images in more detail.', inline=True)
    embed.add_field(name='/setup', value='Open the main control dashboard.', inline=True)
    embed.add_field(name='/panel', value='Open the dashboard again.', inline=True)
    embed.add_field(name='/status', value='Inspect runtime state and asset health.', inline=True)
    embed.add_field(name='/voice_afk', value='Join your current voice channel in silent AFK mode.', inline=True)
    embed.add_field(name='/voice_join', value='Alias of `/voice_afk` for convenience.', inline=True)
    embed.add_field(name='/voice_leave', value='Leave the current voice channel.', inline=True)
    return embed


def gallery_embed(mode: str, icon_names: list[str]) -> discord.Embed:
    listed = '\n'.join(f'• `{name}`' for name in icon_names[:36]) or 'No icons found.'
    embed = shell('Asset Gallery', 'Bundled visuals that back the command center, image analysis surface, and AFK presence cards.', mode)
    embed.add_field(name='Icon Catalog', value=listed[:1024], inline=False)
    embed.add_field(name='Brand Surface', value='Avatar + banner are bundled inside `bot_ui/brand/`.', inline=False)
    return embed


def vision_embed(mode: str) -> discord.Embed:
    embed = shell('Vision Guide', 'Use Mythic for deeper image analysis in Arabic or English.', mode)
    embed.add_field(
        name='What Mythic Checks',
        value=(
            '• Objects and scene composition\n'
            '• Visible text / OCR hints\n'
            '• UI layout and screenshot structure\n'
            '• Colors, style, mood, and branding clues\n'
            '• Notable anomalies, labels, or hidden details'
        ),
        inline=False,
    )
    embed.add_field(
        name='Best Prompt Style',
        value='Ask for exactly what you want: summarize, extract text, explain the UI, list errors, or compare images.',
        inline=False,
    )
    return embed


def transcript_embed(mode: str, source_name: str, transcript: str, language_code: str | None) -> discord.Embed:
    embed = shell('Transcript', transcript[:4000] or '[empty transcript]', mode)
    embed.add_field(name='Source', value=source_name, inline=True)
    embed.add_field(name='Language', value=language_code or 'auto', inline=True)
    return embed
