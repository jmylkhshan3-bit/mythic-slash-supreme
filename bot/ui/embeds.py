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


def loading_embed(mode: str, line: str, prompt: str, user_name: str, is_creator: bool = False) -> discord.Embed:
    title = 'Creator Response Engine' if is_creator else 'Response Engine'
    embed = shell(title, line, mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.add_field(name='User', value=user_name[:256], inline=True)
    if is_creator:
        embed.add_field(name='Creator Link', value='My creator is connected to the response core.', inline=False)
    return embed


def response_embed(mode: str, prompt: str, answer: str, user_name: str, is_creator: bool = False) -> discord.Embed:
    title = 'Creator Reply' if is_creator else 'AI Reply'
    embed = shell(title, answer[:4000], mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    if is_creator:
        embed.add_field(name='Requested by', value=f'{user_name[:220]} • Creator', inline=True)
        embed.add_field(name='Creator Status', value='Supreme creator privileges are active.', inline=True)
    else:
        embed.add_field(name='Requested by', value=user_name[:256], inline=True)
    return embed


def panel_embed(snapshot: dict, mode: str, voice_snapshot: dict[str, object], music_snapshot: dict[str, object], creator_configured: bool) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = shell('Command Center', 'Legendary setup surface for AI, image analysis, file parsing, mention replies, silent AFK voice presence, and direct YouTube audio playback.', mode)
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
        name='Voice Surface',
        value=(
            f'• Status: {voice_line}\n'
            '• AFK join for silent room presence\n'
            '• Manual voice join / leave controls\n'
            '• Voice layer is reused for music playback'
        ),
        inline=False,
    )
    music_line = music_snapshot.get('current_title') or 'Nothing is currently playing'
    embed.add_field(
        name='Music Surface',
        value=(
            f"• Now Playing: `{music_line}`\n"
            f"• Queue Length: `{music_snapshot.get('queue_length', 0)}`\n"
            f"• Loop: `{'ON' if music_snapshot.get('loop_enabled') else 'OFF'}`\n"
            '• Direct YouTube URL playback with yt-dlp'
        ),
        inline=False,
    )
    embed.add_field(
        name='Creator Profile',
        value='Configured and recognized by Discord ID.' if creator_configured else 'Not configured yet. Set CREATOR_IDS in .env / Railway Variables.',
        inline=False,
    )
    embed.add_field(
        name='Main Commands',
        value='Use `/ask`, `/vision`, `/voice_afk`, `/voice_join`, `/voice_leave`, `/music`, `/music_skip`, `/music_stop`, `/music_loop`, `/status`, `/gallery`.',
        inline=False,
    )
    return embed


def status_embed(snapshot: dict, mode: str, asset_status: dict[str, str], model_name: str, voice_snapshot: dict[str, object], music_snapshot: dict[str, object], creator_configured: bool) -> discord.Embed:
    channels = snapshot.get('allowed_channel_ids', [])
    embed = shell('Status Wall', 'Runtime snapshot, AFK voice state, music queue, creator identity state, and asset health.', mode)
    embed.add_field(name='Mode', value=snapshot.get('mode', 'normal'), inline=True)
    embed.add_field(name='Mention Replies', value='ON' if snapshot.get('mention_enabled') else 'OFF', inline=True)
    embed.add_field(name='Allowed Channels', value=str(len(channels)), inline=True)
    embed.add_field(name='Model', value=model_name, inline=False)
    voice_state = 'connected' if voice_snapshot.get('connected') else 'idle'
    embed.add_field(
        name='Voice',
        value=(
            f'State: `{voice_state}`\n'
            f"Channel: `{voice_snapshot.get('channel_name') or 'none'}`\n"
            f"Style: `{voice_snapshot.get('afk_style', 'idle')}`"
        ),
        inline=False,
    )
    embed.add_field(
        name='Music',
        value=(
            f"Playing: `{music_snapshot.get('current_title') or 'none'}`\n"
            f"Queue: `{music_snapshot.get('queue_length', 0)}`\n"
            f"Loop: `{'ON' if music_snapshot.get('loop_enabled') else 'OFF'}`"
        ),
        inline=False,
    )
    embed.add_field(
        name='Creator',
        value='Configured by Discord ID.' if creator_configured else 'No creator ID configured.',
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


def info_embed(mode: str, model_name: str, icon_count: int, creator_configured: bool) -> discord.Embed:
    embed = shell('Build Profile', 'Mythic is tuned for premium slash UX, richer image analysis, restored mentions, AFK voice support, and direct YouTube audio playback.', mode)
    embed.add_field(name='AI Router', value=model_name, inline=False)
    embed.add_field(name='Voice Mode', value='AFK + music playback', inline=False)
    embed.add_field(name='Creator Identity', value='Configured' if creator_configured else 'Not configured', inline=True)
    embed.add_field(name='Icons Loaded', value=str(icon_count), inline=True)
    embed.add_field(name='Version', value=BOT_VERSION, inline=True)
    return embed


def help_embed(mode: str, creator_configured: bool = False) -> discord.Embed:
    embed = shell('Slash Command Deck', 'Every control is slash-based. Mention replies and DMs are available too.', mode)
    embed.add_field(name='/ask', value='Ask the AI with optional attachment or image context.', inline=True)
    embed.add_field(name='/vision', value='Analyze one to three images in more detail.', inline=True)
    embed.add_field(name='/setup', value='Open the main control dashboard.', inline=True)
    embed.add_field(name='/panel', value='Open the dashboard again.', inline=True)
    embed.add_field(name='/status', value='Inspect runtime state and asset health.', inline=True)
    embed.add_field(name='/voice_afk', value='Join your current voice channel in silent AFK mode.', inline=True)
    embed.add_field(name='/voice_join', value='Join your current voice channel for live playback commands.', inline=True)
    embed.add_field(name='/voice_leave', value='Leave the current voice channel.', inline=True)
    embed.add_field(name='/music', value='Play direct YouTube audio from a URL or video ID.', inline=True)
    embed.add_field(name='/music_skip', value='Skip the current track.', inline=True)
    embed.add_field(name='/music_stop', value='Stop playback and clear the queue.', inline=True)
    embed.add_field(name='/music_loop', value='Toggle loop for the current queue.', inline=True)
    embed.add_field(name='/creator', value='Check whether you are recognized as the creator.', inline=True)
    if creator_configured:
        embed.add_field(name='Creator Mode', value='Recognized creator requests receive elevated respect and bypass server channel locks.', inline=False)
    return embed


def gallery_embed(mode: str, icon_names: list[str]) -> discord.Embed:
    listed = '\n'.join(f'• `{name}`' for name in icon_names[:36]) or 'No icons found.'
    embed = shell('Asset Gallery', 'Bundled visuals that back the command center, image analysis surface, AFK presence cards, music controls, and creator profile.', mode)
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


def music_embed(mode: str, title: str, details: str) -> discord.Embed:
    embed = shell(title, details, mode)
    return embed
