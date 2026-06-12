"""Deepgram option building for batch transcription."""

from typing import Any

from nova.config import (
    DEFAULT_DIARIZE,
    DEFAULT_DICTATION,
    DEFAULT_MEASUREMENTS,
    DEFAULT_SMART_FORMAT,
    MODEL,
)


def build_options(
    *,
    keyterms: list[str] | None = None,
    language: str | None = None,
    smart_format: bool = DEFAULT_SMART_FORMAT,
    dictation: bool = DEFAULT_DICTATION,
    measurements: bool = DEFAULT_MEASUREMENTS,
    diarize: bool = DEFAULT_DIARIZE,
    redact: list[str] | None = None,
    timeout_in_seconds: int | None = None,  # API-only; the UI never passes it
) -> dict[str, Any]:
    """Build the kwargs dict passed to the Deepgram transcribe call.

    `model` and `smart_format` are always sent; off-by-default features are sent only
    when enabled (Deepgram defaults them off). Dictation requires punctuation, so it
    forces `punctuate=True`. `redact` (typed as a single str by the SDK) goes through
    `request_options` as repeated query params; `timeout_in_seconds` merges into the
    same `request_options` dict, which is omitted entirely when both are unset.
    """
    request_options: dict[str, Any] = {}
    if redact:
        request_options["additional_query_parameters"] = {"redact": redact}
    if timeout_in_seconds is not None:
        request_options["timeout_in_seconds"] = timeout_in_seconds
    return {
        "model": MODEL,
        "smart_format": smart_format,
        **({"diarize": True} if diarize else {}),
        **({"measurements": True} if measurements else {}),
        # Dictation requires punctuation, so enable both together.
        **({"dictation": True, "punctuate": True} if dictation else {}),
        **({"keyterm": keyterms} if keyterms else {}),
        **({"language": language} if language else {}),
        **({"request_options": request_options} if request_options else {}),
    }
