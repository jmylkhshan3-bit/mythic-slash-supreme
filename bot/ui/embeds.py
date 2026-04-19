from __future__ import annotations

from datetime import datetime, timezone

import discord

from bot.constants import BOT_VERSION, MODE_PRESETS, PROGRESS_STEPS


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


def apply_branding(embed: discord.Embed, *, has_banner: bool, has_avatar: bool) -> discord.Embed:
    if has_banner:
        embed.set_image(url='attachment://bot_banner_680x240.png')
    if has_avatar:
        embed.set_thumbnail(url='attachment://bot_avatar_1024.png')
    return embed


def progress_bar(step: int, total: int = PROGRESS_STEPS) -> str:
    safe_step = max(0, min(step, total))
    filled = '█' * safe_step
    empty = '░' * (total - safe_step)
    return f'`{filled}{empty}` {int((safe_step / total) * 100)}%'


def shell(title: str, description: str, mode: str) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = discord.Embed(
        title=f'{preset.emoji} {title}',
        description=description,
        color=preset.color,
    )
    embed.set_footer(text=f'Mythic Slash Supreme V3 • {preset.label} • {now_stamp()}')
    return embed


def status_embed(snapshot: dict, mode: str, asset_status: dict[str, str], model_name: str) -> discord.Embed:
    channels = snapshot.get('allowed_channel_ids', [])
    embed = shell('Status Wall', 'Live runtime snapshot, assets, and server controls.', mode)
    embed.add_field(name='Mode', value=snapshot.get('mode', 'normal'), inline=True)
    embed.add_field(name='Mentions', value='ON' if snapshot.get('mention_enabled') else 'OFF', inline=True)
    embed.add_field(name='Locked Channels', value=str(len(channels)), inline=True)
    embed.add_field(name='Model', value=model_name, inline=False)
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


def panel_embed(snapshot: dict, mode: str) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = shell('Command Center', 'Premium slash dashboard with quick controls, live mode switching, and modal tools.', mode)
    embed.add_field(name='Current Mode', value=f"{preset.emoji} {preset.label}", inline=True)
    embed.add_field(name='Mentions', value='Enabled' if snapshot.get('mention_enabled') else 'Disabled', inline=True)
    embed.add_field(name='Channel Locks', value=str(len(snapshot.get('allowed_channel_ids', []))), inline=True)
    embed.add_field(
        name='Quick Actions',
        value=(
            '• Quick Ask modal\n'
            '• Mode selector\n'
            '• Toggle mention replies\n'
            '• Lock or unlock this channel\n'
            '• Open help, profile, and status cards'
        ),
        inline=False,
    )
    return embed


def help_embed(mode: str) -> discord.Embed:
    embed = shell('Slash Command Deck', 'Every control is slash-based. Classic prefix commands are not used in this build.', mode)
    embed.add_field(name='/ask', value='Send a question to the AI.', inline=True)
    embed.add_field(name='/mode', value='Switch the live server mode.', inline=True)
    embed.add_field(name='/setup', value='Open the main control dashboard.', inline=True)
    embed.add_field(name='/status', value='Inspect assets and runtime state.', inline=True)
    embed.add_field(name='/systemnote', value='Set or clear the server note.', inline=True)
    embed.add_field(name='/scene', value='Preview animated lines for a mode.', inline=True)
    embed.add_field(name='/profile', value='Show branding and icon preview.', inline=True)
    embed.add_field(name='/settings', value='Open a modal to edit the note.', inline=True)
    embed.add_field(name='/locks', value='List channel locks or clear them.', inline=True)
    embed.add_field(name='/ping', value='Check API and bot latency.', inline=True)
    embed.add_field(name='/about', value='Show build summary.', inline=True)
    embed.add_field(name='/panel', value='Open the command center again.', inline=True)
    return embed


def info_embed(mode: str, model_name: str, icon_count: int) -> discord.Embed:
    embed = shell('Mythic Profile', 'A premium-feel Discord AI build with richer UI, bundled assets, and animated processing.', mode)
    embed.add_field(name='Version', value=BOT_VERSION, inline=True)
    embed.add_field(name='Model', value=model_name, inline=True)
    embed.add_field(name='Icons', value=str(icon_count), inline=True)
    embed.add_field(
        name='Highlights',
        value=(
            '• Slash-first controls\n'
            '• Everyone can use the controls\n'
            '• OpenRouter AI replies\n'
            '• Animated processing states\n'
            '• Railway-ready internal asset pack'
        ),
        inline=False,
    )
    return embed


def profile_embed(mode: str, asset_status: dict[str, str], icon_names: list[str]) -> discord.Embed:
    embed = shell('Brand Profile', 'Brand assets loaded from the bundled project pack with optional external override.', mode)
    embed.add_field(name='Asset Root', value=f"`{asset_status['root']}`", inline=False)
    embed.add_field(name='Avatar', value=asset_status['avatar'], inline=True)
    embed.add_field(name='Banner', value=asset_status['banner'], inline=True)
    embed.add_field(name='Icons', value=asset_status['icons'], inline=True)
    preview = '\n'.join(f'• {name}' for name in icon_names[:10]) or 'No SVG icons found.'
    embed.add_field(name='Icon Preview', value=preview[:1024], inline=False)
    return embed


def loading_embed(mode: str, frame: str, line: str, prompt: str, user_name: str, step: int) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = shell('Processing', f'{frame} {line}', mode)
    embed.add_field(name='Mode', value=f'{preset.emoji} {preset.label} • {preset.status_label}', inline=True)
    embed.add_field(name='Progress', value=progress_bar(step), inline=True)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.set_author(name=f'Requested by {user_name}')
    return embed


def response_embed(mode: str, prompt: str, answer: str, user_name: str, elapsed: float) -> discord.Embed:
    preset = MODE_PRESETS.get(mode, MODE_PRESETS['normal'])
    embed = shell('AI Reply', answer[:4096], mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.add_field(name='Mode', value=f'{preset.emoji} {preset.label}', inline=True)
    embed.add_field(name='Latency', value=f'{elapsed:.1f}s', inline=True)
    embed.set_author(name=f'Requested by {user_name}')
    return embed


def scene_embed(mode: str, lines: list[str], presence_lines: list[str]) -> discord.Embed:
    embed = shell('Mode Scene Preview', 'Preview of the animated texts and status lines used by this mode.', mode)
    embed.add_field(name='Processing Lines', value='\n'.join(f'• {line}' for line in lines[:8]), inline=False)
    embed.add_field(name='Presence Lines', value='\n'.join(f'• {line}' for line in presence_lines[:8]), inline=False)
    return embed


def about_embed(mode: str, mention_enabled: bool) -> discord.Embed:
    embed = shell('About This Build', 'Mythic Slash Supreme V3 is tuned for a flashy Discord UX without breaking deployment simplicity.', mode)
    embed.add_field(name='Core Idea', value='Slash-first AI bot with modals, views, status cards, and animated reply flow.', inline=False)
    embed.add_field(name='Mention Reply', value='Enabled' if mention_enabled else 'Disabled', inline=True)
    embed.add_field(name='Best For', value='Railway, Termux, and mobile-first setups', inline=True)
    return embed


def ping_embed(mode: str, bot_latency_ms: int, api_latency_ms: int | None) -> discord.Embed:
    embed = shell('Latency Check', 'Quick health check for gateway and AI flow.', mode)
    embed.add_field(name='Gateway', value=f'{bot_latency_ms} ms', inline=True)
    embed.add_field(name='AI Test', value=f'{api_latency_ms} ms' if api_latency_ms is not None else 'Not tested', inline=True)
    embed.add_field(name='State', value='Online and responsive', inline=True)
    return embed


def locks_embed(mode: str, channel_ids: list[int]) -> discord.Embed:
    embed = shell('Channel Locks', 'Channels allowed for mention replies when any locks exist.', mode)
    if channel_ids:
        embed.add_field(name='Locked Channels', value='\n'.join(f'<#{channel_id}>' for channel_id in channel_ids[:25]), inline=False)
    else:
        embed.add_field(name='Locked Channels', value='No channel locks are set.', inline=False)
    return embed
