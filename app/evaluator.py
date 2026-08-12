from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

EVALUATOR_PROMPT = """
You are reviewing an authorized QA call between a simulated patient and a medical-practice AI agent.

Analyze the transcript for meaningful product or conversation-quality issues. Prioritize:
- incorrect scheduling or availability claims
- failure to clarify ambiguous requests
- context/memory failures
- contradictions
- unsafe or overconfident medical guidance
- fabricated office, insurance, medication, or policy facts
- failure to complete/confirm a requested workflow
- poor recovery from corrections
- turn-taking failures visible in the transcript
- confusing, repetitive, or materially unnatural behavior

Do NOT report punctuation, transcription quirks, minor stylistic preferences, or harmless wording.
Do NOT assume a business rule unless the transcript itself establishes it. Mark uncertain candidates accordingly.
The output is a candidate review only; a human will validate against the audio before adding any item to the final bug report.

Return JSON exactly in this shape:
{
  "call_summary": "...",
  "scenario_outcome": "completed|partially_completed|not_completed|unclear",
  "bug_candidates": [
    {
      "title": "...",
      "severity": "critical|high|medium|low",
      "timestamp": "MM:SS or best available",
      "category": "...",
      "what_happened": "...",
      "why_it_matters": "...",
      "expected_behavior": "...",
      "evidence": "...",
      "confidence": 0.0
    }
  ],
  "conversation_quality": {
    "coherence": 1,
    "turn_taking": 1,
    "naturalness": 1,
    "goal_progress": 1,
    "notes": "..."
  }
}

Scores are 1-5.
"""


def evaluate_transcript(transcript_path: Path, scenario_path: Path, api_key: str) -> Path:
    client = OpenAI(api_key=api_key)
    transcript = transcript_path.read_text()
    scenario = scenario_path.read_text()

    response = client.responses.create(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": EVALUATOR_PROMPT}],
            },
            {
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": f"SCENARIO:\n{scenario}\n\nTRANSCRIPT:\n{transcript}",
                }],
            },
        ],
        text={"format": {"type": "json_object"}},
    )

    parsed = json.loads(response.output_text)
    out = transcript_path.parent / "evaluation.json"
    out.write_text(json.dumps(parsed, indent=2))
    return out
