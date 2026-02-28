# Remote URL Transcription

## Summary

Add a third tab ("Remote URL") that lets users transcribe audio files hosted at public URLs using Deepgram's `transcribe_url` API. Supports multiple URLs (one per line), batch-processed like file uploads.

## Approach

Use Deepgram's `transcribe_url` method directly — Deepgram fetches the audio from the remote server. No local download needed.

Rejected alternative: download audio locally then reuse `transcribe_file`. Rejected because it doubles bandwidth, increases memory usage, and adds download error handling complexity.

## UI

- Third tab **"Remote URL"** alongside "Upload File" and "Record Audio"
- `st.text_area` for entering URLs, one per line
- "Transcribe" button, disabled when text area is empty
- `MAX_UPLOADS` (100) limit on number of URLs
- Validation: strip whitespace, skip blank lines, reject URLs not starting with `http://` or `https://`

## Processing

New function `_process_urls(urls: list[str])`:

- Same pattern as `_process_inputs`: shared `DeepgramClient`, loop, error handling, session state storage
- Calls `client.listen.v1.media.transcribe_url` with `{"url": url}` and same `_TRANSCRIBE_OPTS`
- Per-URL failure: `st.error` and continue
- Stores results as `(url, response)` tuples in `st.session_state["responses"]`

## Testing

Mirror existing `TestProcessInputs` tests for the new function:

- Client reuse across batch
- Correct transcribe options
- Session state storage
- Missing API key error
- Partial and total batch failure
- Multi-URL success ordering
- Error message format (URL + exception)

Mock `transcribe_url` on the existing `mock_deepgram_cls` fixture in conftest.
