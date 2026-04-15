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

_AUDIO_EXTENSIONS = (".mp3", ".m4a", ".wav", ".flac", ".ogg")

_TRANSCRIBE_OPTS = dict(
    model="nova-3-medical",
    smart_format=True,
    numerals=True,
    profanity_filter=True,
)


def _transcribe_batch(
    api_key: str, items: list[tuple[str, dict[str, object]]], method: str
):
    """Transcribe a batch of audio sources and store results in session state."""
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
        type=["mp3", "m4a", "wav", "flac", "ogg"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if st.button(
        "Transcribe",
        disabled=not uploaded_files or not api_key,
        key="transcribe_upload",
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
        "Transcribe", disabled=not url_text.strip() or not api_key, key="transcribe_url"
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
                    f"Unrecognized audio extension (supported: wav, mp3, m4a, flac, ogg): {', '.join(no_ext)}"
                )
            _process_urls(api_key, valid)


def _display_response(name: str, response: object) -> None:
    """Display transcription results with metrics and download buttons."""
    channel = response.results.channels[0]
    alt = channel.alternatives[0]

    st.subheader(name)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Confidence", f"{alt.confidence:.1%}")
    col2.metric("Duration", f"{response.metadata.duration:.1f}s")
    col3.metric("Words", len(alt.words))
    col4.metric("Language", channel.detected_language or "N/A")
    st.code(alt.transcript, language=None, wrap_lines=True)
    dl_txt, dl_json = st.columns(2)
    dl_txt.download_button(
        "Download Transcript",
        data=alt.transcript,
        file_name=f"{name}.txt",
        mime="text/plain",
        key=f"download_txt_{name}",
    )
    dl_json.download_button(
        "Download JSON",
        data=response.model_dump_json(indent=4),
        file_name=f"{name}.json",
        mime="application/json",
        key=f"download_json_{name}",
    )


for name, response in st.session_state.get("responses", []):
    _display_response(name, response)
