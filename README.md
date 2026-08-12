# Pretty Good AI — Automated Patient Voice Tester

Python voice bot for the Pretty Good AI AI Engineering Challenge. It calls **only** the authorized assessment number `+1-805-439-8008`, behaves as a realistic patient, records complete calls, creates speaker-diarized transcripts, and produces human-reviewable bug candidates.

## What this repository demonstrates

- Real outbound telephone calls using one Twilio E.164 number
- Bidirectional low-latency voice conversations
- OpenAI Realtime patient simulation with scenario goals rather than fixed scripts
- Hard destination safety lock to `+18054398008`
- Twilio MP3 call recordings
- Speaker-diarized, timestamped transcripts
- Ten distinct QA scenarios
- Post-call issue analysis with mandatory human validation
- Explicit iteration tracking

## Architecture

```text
Scenario
   |
   v
Twilio outbound call ---> +1-805-439-8008
   |
   | bidirectional G.711 μ-law Media Stream
   v
FastAPI WebSocket <----> OpenAI Realtime patient model
   |
   +---- Twilio recording callback ---> recording.mp3
                                          |
                                          v
                               diarized transcription
                                          |
                                          v
                                 transcript.txt/json
                                          |
                                          v
                                  bug candidates
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for design decisions and tradeoffs.

## Safety boundary

The assessment destination is not configurable:

```python
ASSESSMENT_NUMBER = "+18054398008"
```

`validate_destination()` rejects every other destination, and tests enforce that behavior. Use only one value for `TWILIO_PHONE_NUMBER` for the entire assessment.

## Prerequisites

- Python 3.11+
- Twilio account with one voice-capable phone number
- OpenAI API key with Realtime access
- Public HTTPS/WSS endpoint for local development (for example an HTTPS tunnel)
- Pretty Good AI test account created at `pgai.us/athena` for product context

Do **not** call the number shown on the Athena confirmation screen. This repository only targets the assessment number.

## Setup

```bash
git clone <YOUR_PUBLIC_REPOSITORY_URL>
cd pgai-voice-tester

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Fill `.env`:

```dotenv
OPENAI_API_KEY=...
OPENAI_REALTIME_MODEL=gpt-realtime-2.1
OPENAI_REALTIME_VOICE=marin

TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

PUBLIC_BASE_URL=https://YOUR-PUBLIC-HTTPS-HOST
```

Never commit `.env`.

## Start the server

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:

```bash
curl http://127.0.0.1:8000/health
```

Your public tunnel must forward to port `8000`, and `PUBLIC_BASE_URL` must be its HTTPS URL.

## Test before spending call/API credits

```bash
pytest -q
python -m scripts.list_scenarios
```

The safety tests must pass before making any call.

## Make the first call

Do **not** start with the full suite. Validate voice quality using the baseline scenario:

```bash
python -m scripts.run_call --scenario appointment_basic
```

The command prints the Twilio Call SID. Once Twilio reports the recording complete, the server saves:

```text
calls/<CALL_SID>/
├── metadata.json
├── scenario.json
├── status.json
├── recording.json
└── recording.mp3
```

Listen to the **entire MP3** before proceeding. Check naturalness, latency, accidental overlap, interruption behavior, and whether the patient actively steers toward the scenario goal.

## Produce transcript + evaluation

```bash
python -m scripts.process_call --call-sid CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

This adds:

```text
transcript.txt
transcript.json
evaluation.json
```

The diarized speaker labels must be manually checked against the recording before final submission.

## Iteration gate

After Call 01, write the observed problem and change in [`ITERATION_LOG.md`](ITERATION_LOG.md). Make at least one evidence-based improvement before scaling the suite if the call reveals latency, verbosity, VAD, interruption, or scenario-steering problems.

## Ten scenarios

1. `appointment_basic`
2. `reschedule_existing`
3. `cancel_existing`
4. `medication_refill`
5. `hours_location`
6. `insurance_uncertain`
7. `ambiguous_scheduling`
8. `barge_in_correction`
9. `after_hours_request`
10. `context_correction`

Each scenario defines an objective and patient facts, not a line-by-line script.

## Running additional calls

Run individually so each call can be reviewed:

```bash
python -m scripts.run_call --scenario reschedule_existing
```

A suite runner also exists:

```bash
python -m scripts.run_suite --limit 10
```

Use it only after baseline call quality is proven. Quality matters more than firing ten calls quickly.

## Bug validation workflow

1. Listen to `recording.mp3`.
2. Compare the relevant section with `transcript.txt`.
3. Review `evaluation.json` as a **candidate-finding aid**, not ground truth.
4. Reproduce or confirm the issue where practical.
5. Add only meaningful verified issues to `BUG_REPORT.md`.
6. Update `reports/CALL_SUMMARY.md`.

## Submission checklist

- [ ] Public GitHub repository
- [ ] Python source code
- [ ] Clear README and single-call command
- [ ] Architecture explanation
- [ ] `.env.example`
- [ ] No secrets committed
- [ ] Exactly one originating phone number used for all assessment calls
- [ ] Destination always `+18054398008`
- [ ] Minimum 10 full calls
- [ ] Natural coherent conversations
- [ ] MP3/OGG recording for every submitted call
- [ ] Both sides represented in every transcript
- [ ] Human-validated bug report
- [ ] Evidence of iteration
- [ ] Loom #1: project walkthrough, webcam on, under 3 minutes
- [ ] Loom #2: real AI-assisted debugging session, webcam on
- [ ] Both Loom videos public
- [ ] Submission form contains public repo, both public Looms, and the exact E.164 originating number

## Loom walkthrough outline

Keep the walkthrough under three minutes:

1. **Problem + result:** show that the simulator makes a real coherent call.
2. **Architecture:** explain why speech-to-speech Realtime was chosen over chained STT/LLM/TTS.
3. **Live evidence:** show a call folder with MP3 + transcript + evaluation.
4. **One meaningful bug:** play the relevant audio segment and explain impact.
5. **Iteration:** show an early issue, the fix, and the improved result.
6. **Judgment:** explain why automated bug candidates require human audio validation.

## AI debugging Loom

Use a real issue found during testing. A strong debugging prompt is:

> Here are the Twilio WebSocket events and the relevant bridge code from a call where the patient talks over the remote agent. Trace the event flow first. Do not edit code yet. Identify whether the likely cause is queued Twilio playback, interruption handling, or Realtime VAD configuration. Then propose the smallest measurable fix and tell me exactly how to validate it in the next call.

Then implement, run, listen, and compare. Do not stage a fake debugging problem.

## Demo Videos

- **Loom #1 — Project Walkthrough:** https://www.loom.com/share/8b27e2456fb74180aae92851818ffbc1
- **Loom #2 — AI-Assisted Debugging:** Coming soon
