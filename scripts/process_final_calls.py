from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI
from app.config import get_settings

ROOT = Path("final_processed")

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)


def fmt_time(seconds: float) -> str:
    total = int(seconds)
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"


for n in range(1, 11):
    call_name = f"call{n:02d}"
    call_dir = ROOT / call_name
    audio_path = call_dir / "recording.mp3"

    if not audio_path.exists():
        raise SystemExit(f"Missing {audio_path}")

    print(f"\n=== Processing {call_name} ===")

    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="gpt-4o-transcribe-diarize",
            file=audio_file,
            response_format="diarized_json",
            chunking_strategy="auto",
        )

    if hasattr(result, "model_dump"):
        payload = result.model_dump()
    elif isinstance(result, dict):
        payload = result
    else:
        raise RuntimeError(
            f"Unexpected transcription response: {type(result)}"
        )

    (call_dir / "transcript.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )

    segments = payload.get("segments", [])

    lines = []

    for segment in segments:
        start = segment.get("start", 0)
        speaker = segment.get("speaker", "UNKNOWN")
        text = segment.get("text", "").strip()

        if text:
            lines.append(
                f"[{fmt_time(start)}] {speaker}: {text}"
            )

    if not lines:
        # Fallback if segments are absent.
        text = payload.get("text", "").strip()
        if text:
            lines.append(text)

    transcript_path = call_dir / "transcript.txt"
    transcript_path.write_text(
        "\n".join(lines) + "\n"
    )

    print("Saved:", transcript_path)
    print("Segments:", len(segments))

print("\n✓ All 10 transcripts processed.")
