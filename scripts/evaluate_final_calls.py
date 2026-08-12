from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI
from app.config import get_settings

ROOT = Path("final_processed")

SCENARIOS = {
    "call01": "Fresh appointment scheduling",
    "call02": "Reschedule an existing appointment",
    "call03": "Cancel an existing appointment",
    "call04": "Medication refill request",
    "call05": "Office hours and location",
    "call06": "Insurance coverage question",
    "call07": "Ambiguous scheduling request",
    "call08": "Preference correction during scheduling",
    "call09": "Unusual 2:00 AM after-hours appointment request",
    "call10": "Context tracking after changing availability",
}

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

for n in range(1, 11):
    call_name = f"call{n:02d}"
    call_dir = ROOT / call_name
    transcript_path = call_dir / "transcript.txt"

    if not transcript_path.exists():
        raise SystemExit(f"Missing {transcript_path}")

    transcript = transcript_path.read_text()

    prompt = f"""
You are reviewing a voice-AI QA call for an AI engineering assessment.

Scenario:
{SCENARIOS[call_name]}

Transcript:
{transcript}

Evaluate ONLY what is supported by the transcript.

Return a JSON object with these exact keys:

{{
  "call": "{call_name}",
  "scenario": "{SCENARIOS[call_name]}",
  "conversation_quality": {{
    "coherent": true,
    "natural_turn_taking": true,
    "patient_stayed_in_character": true,
    "goal_reached": true,
    "notes": ""
  }},
  "bugs": [
    {{
      "title": "",
      "severity": "Low|Medium|High|Critical",
      "timestamp": "",
      "what_happened": "",
      "why_it_matters": "",
      "expected_behavior": ""
    }}
  ],
  "positive_behavior": [],
  "manual_review_notes": ""
}}

Important rules:
- Do not invent bugs.
- Do not treat transcription artifacts as confirmed bugs.
- Focus on meaningful product issues, not punctuation or wording nitpicks.
- Useful categories include scheduling mistakes, stale state, incorrect confirmations,
  hallucinated business information, unsafe medication handling, insurance overclaiming,
  failure to clarify ambiguity, poor interruption handling, and capability misrepresentation.
- If no meaningful bug is supported, return an empty bugs array.
- Timestamps must come from the transcript.
- Be concise.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt,
    )

    raw = response.output_text.strip()

    # Strip accidental markdown fences if present.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].lstrip()

    try:
        evaluation = json.loads(raw)
    except json.JSONDecodeError:
        # Preserve raw model output for debugging.
        (call_dir / "evaluation-raw.txt").write_text(raw + "\n")
        raise RuntimeError(
            f"{call_name}: model did not return valid JSON. "
            f"Saved raw output to {call_dir / 'evaluation-raw.txt'}"
        )

    out = call_dir / "evaluation.json"
    out.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n"
    )

    print(
        f"{call_name}: "
        f"{len(evaluation.get('bugs', []))} candidate bug(s)"
    )

print("\n✓ Evaluated all 10 calls.")
