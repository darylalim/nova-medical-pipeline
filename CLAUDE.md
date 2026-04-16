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

1. Loads `DEEPGRAM_API_KEY` from `.env` via python-dotenv; prompts inline if missing
2. `_TRANSCRIBE_OPTS` — shared dict of Deepgram API options (model, smart format, numerals, profanity filter)
3. `_LOW_CONF_THRESHOLD` — 0.90 confidence threshold for flagging words
4. `_render_transcript_html(words)` — joins Deepgram per-word objects into HTML, wrapping words below threshold in `<mark>`
5. `_transcribe_batch(api_key, items, method)` — creates one shared `DeepgramClient` for a batch, transcribes each item, handles errors via `st.error`, stores results in `st.session_state["responses"]`
6. `_process_inputs(api_key, files)` — wraps `_transcribe_batch` for file uploads
7. `_process_urls(api_key, urls)` — wraps `_transcribe_batch` for remote audio URLs
8. UI with three input tabs (primary full-width Transcribe buttons):
   - **Record** — microphone via `st.audio_input`, max 10 minutes
   - **URL** — transcribe from HTTP/HTTPS URLs, up to 100 URLs per batch
   - **Upload** — up to 100 files, max 2 GB each (mp3, m4a, wav, flac, ogg)
9. `_display_response(name, response, is_first)` — renders each result in a collapsible `st.expander` (first expanded, rest collapsed) with three metrics (confidence, duration, low-confidence word count), highlighted prose transcript, and download buttons (primary .txt, tertiary JSON)

## Testing

Tests mock `DeepgramClient` — no real API calls.

- `conftest.py` (root) — adds repo root to `sys.path` so tests can `import streamlit_app`
- `tests/conftest.py` — shared fixtures (`mock_deepgram_cls`, `mock_st`)
- `tests/test_streamlit_app.py`:
  - `_parse_urls()` — valid/invalid protocols, blank lines, mixed input
  - `_process_inputs()` / `_process_urls()` — client reuse, option passing, session state, partial/total failure, error format, multi-item ordering
  - `_render_transcript_html()` — empty list, all-high/all-low/mixed confidences, boundary at 0.90, punctuated_word usage
  - `_display_response()` — expander label with confidence, expanded/collapsed via is_first, 3 metrics (Confidence, Duration, Low-confidence words), highlighted transcript via st.markdown, no st.code, primary .txt download, tertiary JSON download

## Dependencies

Managed by uv via `pyproject.toml` + `uv.lock`.

Runtime: **deepgram-sdk** (v5), **streamlit**, **python-dotenv**

Dev: **ruff**, **ty**, **pytest**

**deepgram-sdk** notes: options are keyword args (not `PrerecordedOptions`), API key passed explicitly to `DeepgramClient`, responses are Pydantic models.
