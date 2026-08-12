from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI


def _stamp(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def transcribe_call(recording_path: Path, openai_api_key: str) -> tuple[Path, Path]:
    """
    Diarizes the final call recording. Speaker labels are kept as returned
    (for example speaker_0 / speaker_1) until manually verified.
    """
    client = OpenAI(api_key=openai_api_key)

    with recording_path.open("rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe-diarize",
            file=audio_file,
            response_format="diarized_json",
            chunking_strategy="auto",
        )

    raw = transcript.model_dump() if hasattr(transcript, "model_dump") else transcript
    raw_path = recording_path.parent / "transcript.json"
    raw_path.write_text(json.dumps(raw, indent=2, default=str))

    segments = getattr(transcript, "segments", []) or []
    lines = []
    for segment in segments:
        if hasattr(segment, "model_dump"):
            segment = segment.model_dump()
        speaker = str(segment.get("speaker", "speaker")).upper()
        start = float(segment.get("start", 0))
        text = str(segment.get("text", "")).strip()
        if text:
            lines.append(f"[{_stamp(start)}] {speaker}: {text}")

    txt_path = recording_path.parent / "transcript.txt"
    txt_path.write_text("\n\n".join(lines) + "\n")
    return txt_path, raw_path
