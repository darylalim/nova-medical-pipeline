import io
import os
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import streamlit as st
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
MAX_RECORDING_SECONDS = 10 * 60  # 10 minutes
MAX_UPLOADS = 100
MAX_CONCURRENCY = 5

_AUDIO_EXTENSIONS = (".mp3", ".m4a", ".wav", ".flac", ".ogg")
_AUDIO_TYPES = [ext.lstrip(".") for ext in _AUDIO_EXTENSIONS]

_TRANSCRIBE_OPTS = dict(
    model="nova-3-medical",
    smart_format=True,
    numerals=True,
    profanity_filter=True,
)

_LOW_CONF_THRESHOLD = 0.90


def _render_transcript_html(words: list[Any]) -> str:
    """Render Deepgram words as space-joined HTML, wrapping low-confidence words in <mark>."""
    parts = []
    for w in words:
        if w.confidence < _LOW_CONF_THRESHOLD:
            parts.append(f"<mark>{w.punctuated_word}</mark>")
        else:
            parts.append(w.punctuated_word)
    return " ".join(parts)


def _transcribe_batch(
    api_key: str, items: list[tuple[str, dict[str, object]]], method: str
):
    """Transcribe a batch of audio sources in parallel; preserve input order in results."""
    client = DeepgramClient(api_key=api_key)
    transcribe = getattr(client.listen.v1.media, method)
    total = len(items)
    progress = st.progress(0.0, f"Transcribing 0/{total}...")

    indexed: list[tuple[int, str, Any]] = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as executor:
        futures = {
            executor.submit(transcribe, **kwargs, **_TRANSCRIBE_OPTS): (i, label)
            for i, (label, kwargs) in enumerate(items)
        }
        for done, future in enumerate(as_completed(futures), start=1):
            i, label = futures[future]
            progress.progress(done / total, f"Transcribing {done}/{total}...")
            try:
                indexed.append((i, label, future.result()))
            except Exception as e:
                st.error(f"Transcription failed for {label}: {e}")

    progress.empty()

    if indexed:
        indexed.sort(key=lambda r: r[0])
        st.session_state["responses"] = [(label, resp) for _, label, resp in indexed]


def _process_inputs(api_key: str, files: list[tuple[str, bytes]]):
    """Transcribe files with a shared client and store results in session state."""
    items = [(name, {"request": data}) for name, data in files]
    _transcribe_batch(api_key, items, "transcribe_file")


def _process_urls(api_key: str, urls: list[str]):
    """Transcribe remote audio URLs with a shared client and store results in session state."""
    items = [(url, {"url": url}) for url in urls]
    _transcribe_batch(api_key, items, "transcribe_url")


def _parse_urls(text: str) -> tuple[list[str], list[str]]:
    """Parse newline-separated text into (valid_urls, invalid_urls)."""
    raw = [line.strip() for line in text.splitlines()]
    urls = [u for u in raw if u]
    valid = [u for u in urls if u.startswith(("http://", "https://"))]
    invalid = [u for u in urls if not u.startswith(("http://", "https://"))]
    return valid, invalid


st.title("Nova Medical Pipeline")

api_key = os.environ.get("DEEPGRAM_API_KEY", "")
if not api_key:
    st.warning("Deepgram API key required. Get a free key at https://deepgram.com.")
    api_key = st.text_input(
        "Deepgram API Key",
        type="password",
        label_visibility="collapsed",
    )

tab_record, tab_url, tab_upload = st.tabs(["Record", "URL", "Upload"])

with tab_upload:
    uploaded_files = st.file_uploader(
        "Upload audio files",
        type=_AUDIO_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if st.button(
        "Transcribe",
        disabled=not uploaded_files or not api_key,
        key="transcribe_upload",
        type="primary",
        use_container_width=True,
    ):
        if len(uploaded_files) > MAX_UPLOADS:
            st.error(f"Too many files. Maximum is {MAX_UPLOADS} per batch.")
        else:
            oversized = [f.name for f in uploaded_files if f.size > MAX_FILE_SIZE]
            if oversized:
                st.error(f"Skipped (exceeds 2 GB): {', '.join(oversized)}")
            valid = [
                (f.name, f.getvalue())
                for f in uploaded_files
                if f.size <= MAX_FILE_SIZE
            ]
            if valid:
                _process_inputs(api_key, valid)

with tab_record:
    recording = st.audio_input("Record a dictation", label_visibility="collapsed")
    if (
        st.button(
            "Transcribe",
            disabled=recording is None or not api_key,
            key="transcribe_record",
            type="primary",
            use_container_width=True,
        )
        and recording is not None
    ):
        audio_bytes = recording.getvalue()
        with wave.open(io.BytesIO(audio_bytes)) as wf:
            duration = wf.getnframes() / wf.getframerate()
        if duration > MAX_RECORDING_SECONDS:
            st.error("Recording exceeds the 10-minute limit.")
        else:
            _process_inputs(api_key, [("Recording", audio_bytes)])

with tab_url:
    url_text = st.text_area(
        "Enter audio file URLs (one per line)",
        placeholder="https://example.com/audio.mp3\nhttps://example.com/another.mp3",
        label_visibility="collapsed",
    )
    if st.button(
        "Transcribe",
        disabled=not url_text.strip() or not api_key,
        key="transcribe_url",
        type="primary",
        use_container_width=True,
    ):
        valid, invalid = _parse_urls(url_text)
        if invalid:
            st.error(f"Invalid URL(s): {', '.join(invalid)}")
        elif len(valid) > MAX_UPLOADS:
            st.error(f"Too many URLs. Maximum is {MAX_UPLOADS} per batch.")
        else:
            no_ext = [
                u
                for u in valid
                if not u.split("?")[0].lower().endswith(_AUDIO_EXTENSIONS)
            ]
            if no_ext:
                st.warning(
                    f"Unrecognized audio extension (supported: {', '.join(_AUDIO_TYPES)}): {', '.join(no_ext)}"
                )
            _process_urls(api_key, valid)


def _display_response(name: str, response: Any, is_first: bool = False) -> None:
    """Display a single transcription result inside a collapsible expander."""
    channel = response.results.channels[0]
    alt = channel.alternatives[0]

    low_conf_count = sum(1 for w in alt.words if w.confidence < _LOW_CONF_THRESHOLD)

    label = f"{name}  ·  {alt.confidence:.1%}"
    with st.expander(label, expanded=is_first):
        col1, col2, col3 = st.columns(3)
        col1.metric("Confidence", f"{alt.confidence:.1%}")
        col2.metric("Duration", f"{response.metadata.duration:.1f}s")
        col3.metric("Low-confidence words", low_conf_count)

        st.markdown(_render_transcript_html(alt.words), unsafe_allow_html=True)

        dl_txt, dl_json = st.columns(2)
        dl_txt.download_button(
            "Download .txt",
            data=alt.transcript,
            file_name=f"{name}.txt",
            mime="text/plain",
            type="primary",
            key=f"download_txt_{name}",
        )
        dl_json.download_button(
            "JSON",
            data=response.model_dump_json(indent=4),
            file_name=f"{name}.json",
            mime="application/json",
            type="tertiary",
            key=f"download_json_{name}",
        )


for i, (name, response) in enumerate(st.session_state.get("responses", [])):
    _display_response(name, response, is_first=(i == 0))
