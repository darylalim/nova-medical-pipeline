# Streamlit UI Design

## Approach

Replace `main.py` CLI with a Streamlit app (Approach A). Single-file architecture preserved.

## UI Layout

- `st.title` — "Medical Dictation Transcriber"
- `st.file_uploader` — accepts wav, mp3, m4a, flac, ogg
- `st.button` — "Transcribe" (disabled until file uploaded)
- `st.columns` with `st.metric` — confidence, duration, word count, detected language
- `st.text_area` — read-only transcript display
- `st.download_button` — download full JSON response

## Data Flow

1. User uploads audio via `st.file_uploader` -> bytes in session state
2. "Transcribe" button calls `transcribe(audio_bytes)` helper
3. Helper creates `DeepgramClient`, calls API, returns Pydantic response
4. Response stored in `st.session_state` to survive reruns
5. Metrics extracted: confidence, duration (metadata), word count (words list), detected language
6. Full JSON available via `st.download_button`

## Error Handling

- Missing `DEEPGRAM_API_KEY` -> `st.error`
- API failure -> `st.error` with exception message

## Testing

`transcribe()` is a pure function (bytes in, response out) — testable without Streamlit. Existing test scenarios adapt to new signature.

## Files Changed

- `main.py` — rewrite as Streamlit app
- `tests/test_main.py` — update for `transcribe()` helper
- `tests/conftest.py` — update fixtures
- `CLAUDE.md` — update run command
