# Final Call Results

Ten final assessment calls were completed using the same simulated patient identity, Alex Morgan.

Each final call includes:
- the original two-sided MP3 recording,
- a diarized text transcript,
- structured transcript JSON,
- and an automated evaluation.

## Scenario Coverage

| Call | Scenario |
|---|---|
| 01 | Fresh appointment scheduling |
| 02 | Reschedule an existing appointment |
| 03 | Cancel an existing appointment |
| 04 | Medication refill request |
| 05 | Office hours and location |
| 06 | Insurance coverage question |
| 07 | Ambiguous scheduling request |
| 08 | Preference correction during scheduling |
| 09 | Unusual 2:00 AM appointment request |
| 10 | Context tracking after changing availability |

## Automated Evaluation

The conservative transcript-based evaluator reported zero confirmed product bugs in the final selected recordings.

This does not mean no issues were encountered during development. Earlier test calls exposed multiple voice-quality, turn-taking, state-management, and patient-simulation problems. Those observations drove iterative improvements before the final ten recordings were selected.

Audio quality was also reviewed manually because transcript-only evaluation cannot reliably identify clipping, stuttering, awkward latency, or simultaneous speech.
