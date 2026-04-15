# CLAUDE.md

## Project Overview

Streamlit web app that transcribes medical dictation using Deepgram's Nova-3 Medical model.

## Commands

```bash
uv sync                              # Install dependencies
uv run streamlit run streamlit_app.py # Run app
uv run ruff check .                   # Lint
uv run ruff format .                  # Format
uv run ty check .                     # Type check
uv run pytest                         # Test
```

## Architecture

Single-file Streamlit app (`streamlit_app.py`):

1. Loads `DEEPGRAM_API_KEY` from sidebar input (falls back to `.env` via python-dotenv)
2. `_TRANSCRIBE_OPTS` — shared dict of Deepgram API options (model, smart format, numerals, profanity filter)
3. `_transcribe_batch(api_key, items, method)` — creates one shared `DeepgramClient` for a batch, transcribes each item, handles errors via `st.error`, stores results in `st.session_state["responses"]`
4. `_process_inputs(api_key, files)` — wraps `_transcribe_batch` for file uploads
5. `_process_urls(api_key, urls)` — wraps `_transcribe_batch` for remote audio URLs
6. UI with three input tabs:
   - **Record Audio** — microphone via `st.audio_input`, max 10 minutes
   - **Remote URL** — transcribe from HTTP/HTTPS URLs, up to 100 URLs per batch
   - **Upload File** — up to 100 files, max 2 GB each (wav, mp3, m4a, flac, ogg)
7. `_display_response(name, response)` — displays per-file metrics (confidence, duration, word count, language), transcript, and download buttons (text and JSON)

## Testing

Tests mock `DeepgramClient` — no real API calls.

- `conftest.py` (root) — adds repo root to `sys.path` so tests can `import streamlit_app`
- `tests/conftest.py` — shared fixtures (`mock_deepgram_cls`, `mock_st`)
- `tests/test_streamlit_app.py`:
  - `_parse_urls()` — valid/invalid protocols, blank lines, mixed input
  - `_process_inputs()` / `_process_urls()` — client reuse, option passing, session state, partial/total failure, error format, multi-item ordering
  - `_display_response()` — metrics, transcript rendering, text and JSON downloads

## Dependencies

Managed by uv via `pyproject.toml` + `uv.lock`.

Runtime: **deepgram-sdk** (v5), **streamlit**, **python-dotenv**

Dev: **ruff**, **ty**, **pytest**

**deepgram-sdk** notes: options are keyword args (not `PrerecordedOptions`), API key passed explicitly to `DeepgramClient`, responses are Pydantic models.
