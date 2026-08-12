from __future__ import annotations

import argparse
from pathlib import Path

from app.config import CALLS_DIR, get_settings
from app.evaluator import evaluate_transcript
from app.transcription import transcribe_call


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe and evaluate a completed call.")
    parser.add_argument("--call-sid", required=True)
    args = parser.parse_args()

    settings = get_settings()
    call_dir = CALLS_DIR / args.call_sid
    recording = call_dir / "recording.mp3"
    scenario = call_dir / "scenario.json"

    if not recording.exists():
        raise SystemExit(f"Missing {recording}. Wait until the recording callback has completed.")
    if not scenario.exists():
        raise SystemExit(f"Missing {scenario}.")

    transcript_txt, _ = transcribe_call(recording, settings.openai_api_key)
    evaluation = evaluate_transcript(
        transcript_txt, scenario, settings.openai_api_key
    )
    print(f"Transcript: {transcript_txt}")
    print(f"Evaluation: {evaluation}")
    print("IMPORTANT: listen to recording.mp3 before promoting any candidate to BUG_REPORT.md.")


if __name__ == "__main__":
    main()
