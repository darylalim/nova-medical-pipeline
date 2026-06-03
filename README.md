# Nova Medical Pipeline

Transcribe audio files with the Deepgram Nova-3 Medical model.

## Setup

1. Install dependencies: `uv sync`
2. (Optional) Create `.env` at project root with `DEEPGRAM_API_KEY=your-key-here` so the app can use it automatically (otherwise it prompts inline at startup)

## Usage

```bash
uv run streamlit run streamlit_app.py
```

If `DEEPGRAM_API_KEY` is not set, the app prompts for it inline.

**Select audio** from the input tabs at the top:

- **Upload** — up to 100 audio files (mp3, m4a, wav, flac, ogg; max 2 GB each)
- **Record** — record from microphone (max 10 minutes)
- **URL** — transcribe from HTTP/HTTPS URLs (up to 100 per batch)

Below the input, a **Features** panel (left) holds the request options, with a **Run** button at the bottom. If you populate more than one input tab, Run transcribes a single one by priority — **Upload, then Record, then URL** — and shows a notice naming which ran and which were ignored.

- **Language** — English variants (Nova-3 Medical is English-only)
- **Smart Format** (on by default) — punctuation, paragraph breaks, and entity formatting
- **Keyterm Prompting** — type specialized vocabulary (drug names, procedures, names), Enter to add each, up to 100, to boost recognition
- **Diarize** (off by default) — labels speaker turns as Speaker 1, Speaker 2, … in the transcript (speakers are numbered, not named by role)
- **Dictation** (off by default) — turns spoken commands like "period" / "new paragraph" into punctuation (also enables punctuation)
- **Measurements** (off by default) — abbreviates spoken units (e.g. "five milligrams" → "5 mg")
- **Redact** (none by default) — replaces selected information with redaction tags. Use **PII** to de-identify (names, locations, IDs); note **PHI** strips clinical content itself (conditions, drugs, injuries)

Once a request completes, the **Transcript** and **JSON** tabs (right) display the response. A single result shows an audio player pinned above the scrollable text; multiple results are labeled and divided per file. With **Diarize** on, the transcript is split into `Speaker 1:`, `Speaker 2:`, … lines. (Large uploads — over 25 MB — skip the inline player to limit memory; recordings and URLs always have one.)

## Sample Audio

Medical dictation practice files from [NCH Software](https://www.nch.com.au/scribe/practice.html):

- [Chris Smith Medical Report](https://www.nch.com.au/scribe/practice/audio-sample-4.mp3)
- [Janet Jones Medical Report](https://www.nch.com.au/scribe/practice/audio-sample-5.mp3)
- [John Finton Medical Report](https://www.nch.com.au/scribe/practice/audio-sample-6.mp3)

## Testing

```bash
uv run pytest
```

Tests mock the Deepgram API — no real API calls are made. Covers input validation, batch processing, error handling, and session state management.
