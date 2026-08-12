# Iteration Log

## 1. Twilio Media Stream connection

### Problem
Initial calls terminated almost immediately because the Twilio Media Stream WebSocket was rejected.

### Diagnosis
The scenario identifier was being passed through the Media Stream URL rather than through Twilio custom stream parameters.

### Change
Moved the scenario identifier into a Twilio `<Parameter>` and resolved it from `start.customParameters`.

### Result
Twilio successfully connected to the bidirectional WebSocket and the OpenAI Realtime session initialized correctly.

---

## 2. Mid-sentence audio interruption

### Problem
Patient speech was occasionally cut off.

### Diagnosis
The bridge cleared Twilio's outbound audio buffer too aggressively when remote speech was detected.

### Change
Removed unconditional audio clearing and adjusted turn-detection behavior.

### Result
Patient responses became substantially less prone to mid-sentence truncation.

---

## 3. Identity consistency

### Problem
The simulated patient initially lacked a fixed DOB and later failed to correct an incorrect DOB confirmation. Name spelling was also inconsistent.

### Change
Added fixed identity fields to scenarios:
- name,
- first and last name,
- exact spelling,
- date of birth,
- callback number.

Added explicit instructions to correct incorrect confirmations immediately.

### Result
Identity information remained consistent across subsequent calls.

---

## 4. Phone-number naturalness

### Problem
The patient spoke the stored E.164 `+1` prefix aloud.

### Change
Kept E.164 internally while instructing the patient to speak the normal ten-digit North American number unless explicitly asked for the country code.

### Result
Phone-number responses sounded more natural.

---

## 5. Prompt leakage

### Problem
The patient occasionally verbalized internal testing logic, including language about avoiding duplicate appointments.

### Change
Separated silent behavior instructions from spoken dialogue and explicitly prohibited discussion of scenarios, QA, prompts, implementation details, or testing strategy.

### Result
Patient dialogue became more realistic and concise.

---

## 6. Last-turn grounding

### Problem
The patient occasionally used a generic acknowledgment instead of answering the clinic agent's latest question.

### Change
Added instructions to identify and directly answer the most recent completed question.

### Result
Closing and clarification turns became more contextually appropriate.

---

## 7. Response latency and turn-taking

### Problem
Aggressive turn detection could cause interruption, while conservative settings could create noticeable latency.

### Change
Iteratively tuned Realtime voice-activity detection and concise-response instructions.

### Result
The final configuration provided a better balance between responsiveness and avoiding overlap.

---

## 8. Scenario realism

### Problem
Early scenarios used different patient identities despite all calls originating from one test number, and some scenario facts did not match the clinic context.

### Change
Standardized the simulated patient as Alex Morgan and adjusted scenarios to form realistic workflows.

### Result
Calls became more internally consistent and easier to evaluate.

---

## 9. Recording and transcription pipeline

### Problem
Some Twilio recording callbacks completed while the expected local MP3 was unavailable, and early transcription tooling had SDK compatibility issues.

### Change
Added recording retrieval workflows, upgraded the OpenAI SDK, and created a final batch diarization/transcription pipeline.

### Result
Ten unique final MP3 recordings were collected and each produced both text and structured transcripts.

---

## 10. Final validation

The final recording set was checked for:
- exactly 10 MP3 recordings,
- unique SHA-256 hashes,
- non-empty transcripts,
- two-sided conversation coverage,
- scenario variety,
- and manual voice-quality review.

All ten final recordings passed the artifact-integrity checks.
