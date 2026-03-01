import io
import os
import wave

import streamlit as st
from deepgram import DeepgramClient
from dotenv import load_dotenv

load_dotenv()

MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
MAX_RECORDING_SECONDS = 10 * 60  # 10 minutes
MAX_UPLOADS = 100

_AUDIO_EXTENSIONS = (".wav", ".mp3", ".m4a", ".flac", ".ogg")

_TRANSCRIBE_OPTS = dict(
    model="nova-3-medical",
    smart_format=True,
    numerals=True,
    profanity_filter=True,
)


def _transcribe_batch(items: list[tuple[str, dict[str, object]]], method: str):
    """Transcribe a batch of audio sources and store results in session state."""
    try:
        api_key = os.environ["DEEPGRAM_API_KEY"]
    except KeyError:
        st.error("Missing DEEPGRAM_API_KEY. Set it in a .env file at the project root.")
        return
    client = DeepgramClient(api_key=api_key)
    responses = []
    for label, kwargs in items:
        try:
            with st.spinner(f"Transcribing {label}..."):
                transcribe = getattr(client.listen.v1.media, method)
                resp = transcribe(**kwargs, **_TRANSCRIBE_OPTS)
                responses.append((label, resp))
        except Exception as e:
            st.error(f"Transcription failed for {label}: {e}")
    if responses:
        st.session_state["responses"] = responses


def _process_inputs(files: list[tuple[str, bytes]]):
    """Transcribe files with a shared client and store results in session state."""
    items = [(name, {"request": data}) for name, data in files]
    _transcribe_batch(items, "transcribe_file")


def _process_urls(urls: list[str]):
    """Transcribe remote audio URLs with a shared client and store results in session state."""
    items = [(url, {"url": url}) for url in urls]
    _transcribe_batch(items, "transcribe_url")


def _parse_urls(text: str) -> tuple[list[str], list[str]]:
    """Parse newline-separated text into (valid_urls, invalid_urls)."""
    raw = [line.strip() for line in text.splitlines()]
    urls = [u for u in raw if u]
    valid = [u for u in urls if u.startswith(("http://", "https://"))]
    invalid = [u for u in urls if not u.startswith(("http://", "https://"))]
    return valid, invalid


st.title("Medical Dictation Transcriber")

tab_record, tab_url, tab_upload = st.tabs(["Record Audio", "Remote URL", "Upload File"])

with tab_upload:
    uploaded_files = st.file_uploader(
        "Upload audio files",
        type=["wav", "mp3", "m4a", "flac", "ogg"],
        accept_multiple_files=True,
    )
    if st.button("Transcribe", disabled=not uploaded_files, key="transcribe_upload"):
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
                _process_inputs(valid)

with tab_record:
    recording = st.audio_input("Record a dictation")
    if (
        st.button("Transcribe", disabled=recording is None, key="transcribe_record")
        and recording is not None
    ):
        audio_bytes = recording.getvalue()
        with wave.open(io.BytesIO(audio_bytes)) as wf:
            duration = wf.getnframes() / wf.getframerate()
        if duration > MAX_RECORDING_SECONDS:
            st.error("Recording exceeds the 10-minute limit.")
        else:
            _process_inputs([("Recording", audio_bytes)])

with tab_url:
    url_text = st.text_area(
        "Enter audio file URLs (one per line)",
        placeholder="https://example.com/audio.wav",
    )
    if st.button("Transcribe", disabled=not url_text.strip(), key="transcribe_url"):
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
                    f"Unrecognized audio extension (supported: wav, mp3, m4a, flac, ogg): {', '.join(no_ext)}"
                )
            _process_urls(valid)

for name, response in st.session_state.get("responses", []):
    channel = response.results.channels[0]
    alt = channel.alternatives[0]

    st.subheader(name)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Confidence", f"{alt.confidence:.1%}")
    col2.metric("Duration", f"{response.metadata.duration:.1f}s")
    col3.metric("Words", len(alt.words))
    col4.metric("Language", channel.detected_language or "N/A")
    st.text_area(
        name,
        value=alt.transcript,
        height=300,
        disabled=True,
        label_visibility="collapsed",
    )
    st.download_button(
        "Download JSON",
        data=response.model_dump_json(indent=4),
        file_name=f"{name}.json",
        mime="application/json",
        key=f"download_{name}",
    )
