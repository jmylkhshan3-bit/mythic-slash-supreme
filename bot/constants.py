from __future__ import annotations

from dataclasses import dataclass

BOT_VERSION = '3.0.0'
SPINNER_FRAMES = ['◐', '◓', '◑', '◒', '✦', '✧']
PROGRESS_STEPS = 12


@dataclass(frozen=True, slots=True)
class ModePreset:
    key: str
    label: str
    emoji: str
    color: int
    style_prompt: str
    loading_lines: list[str]
    presence_lines: list[str]
    status_label: str


MODE_PRESETS: dict[str, ModePreset] = {
    'normal': ModePreset(
        key='normal',
        label='Normal',
        emoji='⚡',
        color=0x4CC9F0,
        style_prompt='Balanced, useful, clear, and direct.',
        status_label='stable',
        loading_lines=[
            'Stabilizing the reply lane...', 'Reading the message pulse...', 'Scanning the request...', 'Aligning response blocks...',
            'Cooling the latency core...', 'Opening the answer channel...', 'Building a precise reply...', 'Calibrating clarity...',
            'Normal mode is assembling the answer...', 'Streaming response fragments...', 'Checking context anchors...', 'Polishing the final wording...',
            'Keeping it sharp and direct...', 'Filtering noise...', 'Routing signal to output...', 'Setting confidence rails...',
            'Packing the clean response...', 'Reviewing message structure...', 'Locking the final answer...', 'Delivery lane ready...'
        ],
        presence_lines=[
            'bot is online', 'bot is reading the room', 'bot is checking prompts', 'bot is routing replies', 'bot is keeping it smooth',
            'bot is stabilizing', 'bot is on normal duty', 'bot is syncing slash flow', 'bot is shaping answers', 'bot is keeping replies clean',
            'bot is warming up', 'bot is preparing a clean response', 'bot is monitoring mentions', 'bot is listening', 'bot is sharpening output',
            'bot is tracking chat energy', 'bot is keeping the lanes open', 'bot is ready for asks', 'bot is settling into rhythm', 'bot is running default power'
        ],
    ),
    'thinking': ModePreset(
        key='thinking',
        label='Thinking',
        emoji='🧠',
        color=0x8D99AE,
        style_prompt='Reflective, analytical, and step-aware without exposing hidden reasoning.',
        status_label='deep focus',
        loading_lines=[
            'Thinking mode is mapping the question...', 'Reviewing hidden edges...', 'Tracing the best route...', 'Comparing possible answers...',
            'Checking assumptions...', 'Rebuilding the answer tree...', 'Ranking response paths...', 'Thinking mode is sharpening logic...',
            'Connecting context nodes...', 'Balancing clarity with depth...', 'Reducing ambiguity...', 'Inspecting the phrasing frame...',
            'Pressure-testing the answer...', 'Following the strongest path...', 'Refining the explanation...', 'Compressing the insight...',
            'Preparing the clean conclusion...', 'Rechecking the final draft...', 'Locking the thoughtful response...', 'Thinking lane complete...'
        ],
        presence_lines=[
            'bot is thinking', 'bot is reflecting', 'bot is tracing ideas', 'bot is modeling the answer', 'bot is comparing paths',
            'bot is checking assumptions', 'bot is reading between the lines', 'bot is building insight', 'bot is considering options', 'bot is reasoning quietly',
            'bot is sketching solutions', 'bot is focusing hard', 'bot is sorting context', 'bot is connecting clues', 'bot is weighing explanations',
            'bot is analyzing intent', 'bot is selecting the best angle', 'bot is distilling thought', 'bot is tracking nuance', 'bot is building a deeper reply'
        ],
    ),
    'dev': ModePreset(
        key='dev',
        label='Dev',
        emoji='🛠️',
        color=0x4361EE,
        style_prompt='Technical, implementation-oriented, code-first, and structured.',
        status_label='build mode',
        loading_lines=[
            'Dev mode is porting ideas...', 'Reading the stack trace in spirit...', 'Compiling a cleaner answer...', 'Linting the wording...',
            'Checking implementation gaps...', 'Mapping function flow...', 'Reviewing edge cases...', 'Drafting the technical response...',
            'Optimizing the answer path...', 'Tightening the code logic...', 'Parsing parameters...', 'Preparing dev-grade output...',
            'Linking modules mentally...', 'Checking syntax risk...', 'Building robust guidance...', 'Sweeping for bugs...',
            'Dev mode is closing loose ends...', 'Hardening the response...', 'Final technical pass...', 'Build complete...'
        ],
        presence_lines=[
            'bot is porting', 'bot is debugging', 'bot is checking syntax', 'bot is reading the stack', 'bot is compiling vibes',
            'bot is wiring slash systems', 'bot is tracing variables', 'bot is patching flow', 'bot is hardening logic', 'bot is scanning for bugs',
            'bot is writing clean code', 'bot is optimizing paths', 'bot is reading docs in spirit', 'bot is structuring modules', 'bot is building commands',
            'bot is testing branches', 'bot is tuning architecture', 'bot is booting dev mode', 'bot is shaping implementations', 'bot is in builder state'
        ],
    ),
    'god': ModePreset(
        key='god',
        label='God',
        emoji='👑',
        color=0xF4A261,
        style_prompt='Confident, premium, cinematic, high-energy, and decisive.',
        status_label='legendary',
        loading_lines=[
            'God mode is charging the throne...', 'Summoning a premium-grade answer...', 'Bending the reply space...', 'Elevating the response tier...',
            'Power-routing the output...', 'Infusing cinematic confidence...', 'Polishing the royal answer...', 'Locking the grand delivery...',
            'Scanning the arena...', 'Commanding the response core...', 'Forging the final statement...', 'Driving the signal harder...',
            'Coating the answer in gold...', 'Preparing a dominant reply...', 'Lighting the command deck...', 'God mode is not missing...',
            'Raising output intensity...', 'Finalizing the mythic drop...', 'Crowning the response...', 'Throne sync complete...'
        ],
        presence_lines=[
            'bot is cheating', 'bot is ruling the server', 'bot is on mythic power', 'bot is beyond normal', 'bot is commanding the deck',
            'bot is glowing', 'bot is carrying the lobby', 'bot is breaking limits', 'bot is moving like a boss', 'bot is on crown duty',
            'bot is mythic', 'bot is overpowering latency', 'bot is loading legendary UI', 'bot is flexing clean output', 'bot is steering the whole room',
            'bot is on royal sync', 'bot is maxed out', 'bot is pulling premium energy', 'bot is in supreme mode', 'bot is dominating the response lane'
        ],
    ),
    'creative': ModePreset(
        key='creative',
        label='Creative',
        emoji='🎨',
        color=0xD16BA5,
        style_prompt='Expressive, imaginative, stylish, and idea-rich.',
        status_label='vivid',
        loading_lines=[
            'Creative mode is opening the color vault...', 'Sketching stronger ideas...', 'Blending style with clarity...', 'Painting the reply...',
            'Mixing vivid concepts...', 'Turning sparks into structure...', 'Inventing a cleaner angle...', 'Arranging the creative flow...',
            'Adding flair without losing sense...', 'Polishing the tone palette...', 'Framing a more memorable answer...', 'Spinning ideas into form...',
            'Creative mode is composing momentum...', 'Balancing style and signal...', 'Building a standout reply...', 'Rendering the final scene...',
            'Refining the rhythm...', 'Locking the artistic pass...', 'Packaging the vivid answer...', 'Creative output ready...'
        ],
        presence_lines=[
            'bot is sketching ideas', 'bot is composing a vibe', 'bot is painting replies', 'bot is remixing concepts', 'bot is dreaming in UI',
            'bot is shaping cool answers', 'bot is styling the output', 'bot is blending sparks', 'bot is building something fresh', 'bot is drafting creative energy',
            'bot is finding a new angle', 'bot is turning prompts into scenes', 'bot is on design duty', 'bot is setting the mood', 'bot is flowing',
            'bot is tuning the rhythm', 'bot is crafting a standout reply', 'bot is making ideas glow', 'bot is shaping flavor', 'bot is in concept forge'
        ],
    ),
    'analyst': ModePreset(
        key='analyst',
        label='Analyst',
        emoji='📊',
        color=0x2A9D8F,
        style_prompt='Structured, evidence-minded, comparative, and concise.',
        status_label='precision',
        loading_lines=[
            'Analyst mode is structuring the data...', 'Breaking the request into layers...', 'Sorting facts from noise...', 'Comparing answer candidates...',
            'Building a clean framework...', 'Testing the strongest outline...', 'Reducing clutter...', 'Reading signal density...',
            'Compressing the findings...', 'Preparing a clear breakdown...', 'Aligning categories...', 'Inspecting the details...',
            'Reframing into a useful answer...', 'Tightening the summary...', 'Quantizing the chaos...', 'Linking the evidence blocks...',
            'Drafting a clearer comparison...', 'Reviewing the logic rails...', 'Final analytic pass...', 'Analyst output complete...'
        ],
        presence_lines=[
            'bot is analyzing', 'bot is sorting data', 'bot is checking patterns', 'bot is reading the signal', 'bot is comparing options',
            'bot is structuring answers', 'bot is distilling findings', 'bot is building a framework', 'bot is on analysis duty', 'bot is reducing noise',
            'bot is tightening logic', 'bot is ranking outcomes', 'bot is splitting the problem', 'bot is evaluating clues', 'bot is examining context',
            'bot is lining up evidence', 'bot is extracting the core', 'bot is shaping the summary', 'bot is mapping the details', 'bot is preparing clean insight'
        ],
    ),
}

MODE_CHOICES: list[tuple[str, str]] = [(preset.label, preset.key) for preset in MODE_PRESETS.values()]
