"""Generate silent WAV test files.

Run once to create the files, then commit them to git:
    uv run python tests/data/audio/generate.py
"""

import struct
import wave
from pathlib import Path

DIR = Path(__file__).parent


def _write_silence(filename: str, *, duration_s: float, channels: int = 1) -> None:
    sample_rate = 16_000
    sample_width = 2  # 16-bit
    num_frames = int(sample_rate * duration_s)

    path = DIR / filename
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        # Write all-zero samples (silence)
        wf.writeframes(struct.pack(f"<{num_frames * channels}h", *([0] * num_frames * channels)))

    print(f"Created {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    _write_silence("silence-1s.wav", duration_s=1)
    _write_silence("silence-30s.wav", duration_s=30)
    _write_silence("silence-stereo.wav", duration_s=1, channels=2)
