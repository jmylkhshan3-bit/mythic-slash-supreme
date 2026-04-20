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


def status_embed(snapshot: dict, mode: str, asset_status: dict[str, str], model_name: str) -> discord.Embed:
    channels = snapshot.get('allowed_channel_ids', [])
    embed = shell('Status Wall', 'Runtime snapshot, server controls, official voice routing, and asset health.', mode)
    embed.add_field(name='Mode', value=snapshot.get('mode', 'normal'), inline=True)
    embed.add_field(name='Mention Replies', value='ON' if snapshot.get('mention_enabled') else 'OFF', inline=True)
    embed.add_field(name='Allowed Channels', value=str(len(channels)), inline=True)
    embed.add_field(name='Model', value=model_name, inline=False)
    voice_profile = (
        f"Wake: `{snapshot.get('voice_wake_phrase', 'hey m')}`\n"
        f"Input: `{snapshot.get('voice_input_language', 'auto')}`\n"
        f"Output: `{snapshot.get('voice_output_language', 'auto')}`\n"
        f"Silence: `{snapshot.get('voice_silence_seconds', 2.0)}` sec\n"
        f"Armed: `{'yes' if snapshot.get('voice_armed') else 'no'}`"
    )
    embed.add_field(name='Voice Profile', value=voice_profile, inline=False)
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


def panel_embed(snapshot: dict, mode: str, activation_phrase: str) -> discord.Embed:
    embed = shell('Command Center', 'Legendary control panel for slash commands, mention routing, and official bot voice AI.', mode)
    embed.add_field(name='Current Mode', value=snapshot.get('mode', 'normal'), inline=True)
    embed.add_field(name='Mentions', value='Enabled' if snapshot.get('mention_enabled') else 'Disabled', inline=True)
    embed.add_field(name='Channel Locks', value=str(len(snapshot.get('allowed_channel_ids', []))), inline=True)
    embed.add_field(
        name='AI Surface',
        value=(
            '• Slash ask flow\n'
            '• Mention + direct messages\n'
            f'• Activation phrase: `{activation_phrase}`\n'
            '• Attachment reading and audio transcription'
        ),
        inline=False,
    )
    embed.add_field(
        name='Voice Surface',
        value=(
            '• Official bot runtime only\n'
            '• Join or leave voice\n'
            '• Arm wake-word capture design\n'
            '• Speak AI replies as audio\n'
            '• Transcribe audio attachments'
        ),
        inline=False,
    )
    return embed


def help_embed(mode: str) -> discord.Embed:
    embed = shell('Slash Command Deck', 'Every control is slash-based. Classic prefix commands are ignored.', mode)
    embed.add_field(name='/ask', value='Send a question to the AI.', inline=True)
    embed.add_field(name='/mode', value='Switch the live server mode.', inline=True)
    embed.add_field(name='/setup', value='Open the main control dashboard.', inline=True)
    embed.add_field(name='/panel', value='Open the command center panel again.', inline=True)
    embed.add_field(name='/status', value='Inspect assets and runtime state.', inline=True)
    embed.add_field(name='/voice_action', value='Join, leave, or speak in voice.', inline=True)
    embed.add_field(name='/voice_arm', value='Arm official voice wake mode.', inline=True)
    embed.add_field(name='/voice_disarm', value='Disarm wake mode.', inline=True)
    embed.add_field(name='/voice_status', value='Inspect the voice runtime.', inline=True)
    embed.add_field(name='/transcribe', value='Transcribe an attached audio file.', inline=True)
    embed.add_field(name='/systemnote', value='Set or clear the server note.', inline=True)
    return embed


def info_embed(mode: str, model_name: str, icon_count: int) -> discord.Embed:
    embed = shell('Mythic Profile', 'Premium-feel Discord AI build with slash UI, official voice controls, and attachment analysis.', mode)
    embed.add_field(name='Version', value=BOT_VERSION, inline=True)
    embed.add_field(name='Model', value=model_name, inline=True)
    embed.add_field(name='Icons', value=str(icon_count), inline=True)
    embed.add_field(
        name='Highlights',
        value=(
            '• Slash-first commands\n'
            '• Everyone can use the controls\n'
            '• OpenRouter free router\n'
            '• AssemblyAI transcription\n'
            '• Free TTS playback in voice\n'
            '• Official bot wake-word design'
        ),
        inline=False,
    )
    return embed


def profile_embed(mode: str, asset_status: dict[str, str], icon_names: list[str]) -> discord.Embed:
    embed = shell('Brand Profile', 'Brand assets loaded from internal or external folders.', mode)
    embed.add_field(name='Asset Root', value=f"`{asset_status['root']}`", inline=False)
    embed.add_field(name='Source', value=asset_status['source'], inline=True)
    embed.add_field(name='Avatar', value=asset_status['avatar'], inline=True)
    embed.add_field(name='Banner', value=asset_status['banner'], inline=True)
    preview = '\n'.join(f'• {name}' for name in icon_names[:10]) or 'No SVG icons found.'
    embed.add_field(name='Icon Preview', value=preview[:1024], inline=False)
    return embed


def loading_embed(mode: str, line: str, prompt: str, user_name: str) -> discord.Embed:
    embed = shell('Processing', line, mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.set_author(name=f'Requested by {user_name}')
    return embed


def response_embed(mode: str, prompt: str, answer: str, user_name: str) -> discord.Embed:
    embed = shell('AI Reply', answer[:4096], mode)
    embed.add_field(name='Prompt', value=prompt[:1024], inline=False)
    embed.set_author(name=f'Requested by {user_name}')
    return embed


def scene_embed(mode: str, lines: list[str], presence_lines: list[str]) -> discord.Embed:
    embed = shell('Mode Scene Preview', 'Preview of the animated texts used by this mode.', mode)
    embed.add_field(name='Processing Lines', value='\n'.join(f'• {line}' for line in lines[:8]), inline=False)
    embed.add_field(name='Presence Lines', value='\n'.join(f'• {line}' for line in presence_lines[:8]), inline=False)
    return embed


def voice_hub_embed(
    mode: str,
    *,
    connected_channel: str | None,
    stt_enabled: bool,
    tts_voice: str,
    activation_phrase: str,
    armed: bool,
    receive_supported: bool,
    receive_active: bool,
    input_language: str,
    output_language: str,
    silence_seconds: float,
) -> discord.Embed:
    embed = shell('Voice Hub', 'Official bot voice controls, speech output, and wake-word design tools.', mode)
    embed.add_field(name='Connected Channel', value=connected_channel or 'Not connected', inline=False)
    embed.add_field(name='Armed', value='YES' if armed else 'NO', inline=True)
    embed.add_field(name='Receive Backend', value='Ready' if receive_supported else 'Compatibility', inline=True)
    embed.add_field(name='Listening', value='Active' if receive_active else 'Idle', inline=True)
    embed.add_field(name='Speech to Text', value='Enabled' if stt_enabled else 'Missing ASSEMBLYAI_API_KEY', inline=True)
    embed.add_field(name='TTS Voice', value=tts_voice, inline=True)
    embed.add_field(name='Wake Phrase', value=activation_phrase, inline=True)
    embed.add_field(name='Input Lang', value=input_language, inline=True)
    embed.add_field(name='Output Lang', value=output_language, inline=True)
    embed.add_field(name='Silence Stop', value=f'{silence_seconds:.1f}s', inline=True)
    embed.add_field(
        name='Use It Like This',
        value=(
            '• `/voice_action action:join`\n'
            '• `/voice_arm` after the bot joins voice\n'
            '• speak the wake phrase, then your request\n'
            '• `/voice_action action:speak text:...`\n'
            '• `/transcribe` with an audio attachment'
        ),
        inline=False,
    )
    return embed


def voice_architecture_embed(mode: str, snapshot: dict, runtime_note: str, receive_supported: bool) -> discord.Embed:
    embed = shell('Official Voice Runtime', 'Server-safe design for wake-word capture without a main account.', mode)
    embed.add_field(
        name='Architecture',
        value=(
            '1. official bot joins the voice channel\n'
            '2. wake phrase arms the capture lane\n'
            '3. silence closes the capture window\n'
            '4. speech becomes text\n'
            '5. AI generates the answer\n'
            '6. text becomes voice in the same room'
        ),
        inline=False,
    )
    embed.add_field(
        name='Current Profile',
        value=(
            f"Wake: `{snapshot.get('voice_wake_phrase', 'hey m')}`\n"
            f"Input: `{snapshot.get('voice_input_language', 'auto')}`\n"
            f"Output: `{snapshot.get('voice_output_language', 'auto')}`\n"
            f"Silence: `{snapshot.get('voice_silence_seconds', 2.0)}` sec"
        ),
        inline=False,
    )
    embed.add_field(name='Receive Backend', value='Experimental backend available' if receive_supported else 'Compatibility mode only', inline=False)
    embed.add_field(name='Runtime Note', value=runtime_note[:1024], inline=False)
    return embed


def transcript_embed(mode: str, *, source_name: str, transcript: str, language_code: str | None) -> discord.Embed:
    embed = shell('Transcript Ready', transcript[:4096] or 'No speech detected.', mode)
    embed.add_field(name='Source', value=source_name, inline=True)
    embed.add_field(name='Language', value=language_code or 'unknown', inline=True)
    return embed
