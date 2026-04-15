# Nova Medical Pipeline

Streamlit web app that transcribes medical dictation using Deepgram's Nova-3 Medical model.

## Setup

1. Install dependencies: `uv sync`
2. (Optional) Create `.env` at project root with `DEEPGRAM_API_KEY=your-key-here` to pre-fill the sidebar

## Usage

```bash
uv run streamlit run streamlit_app.py
```

Enter your Deepgram API key in the sidebar. If a `.env` file is present, the key is pre-filled automatically.

- **Record Audio** — record from microphone (max 10 minutes)
- **Remote URL** — transcribe from HTTP/HTTPS URLs (up to 100 per batch)
- **Upload File** — up to 100 audio files (wav, mp3, m4a, flac, ogg; max 2 GB each)

Transcriptions use smart formatting, numerals conversion, and profanity filtering. Each result displays confidence, duration, word count, and detected language, along with the full transcript. Download results as plain text or JSON.

## Sample Audio

Medical dictation practice files from [NCH Software](https://www.nch.com.au/scribe/practice.html):

- [Chris Smith Medical Report](https://www.nch.com.au/scribe/practice/audio-sample-4.mp3)
- [Janet Jones Medical Report](https://www.nch.com.au/scribe/practice/audio-sample-5.mp3)
- [John Finton Medical Report](https://www.nch.com.au/scribe/practice/audio-sample-6.mp3)

## Testing

```bash
uv run pytest
```

Tests mock the Deepgram API — no real API calls are made. Covers batch processing, error handling, and session state management.
