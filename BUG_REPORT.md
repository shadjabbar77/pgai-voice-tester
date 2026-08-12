# Bug Report

## Final Assessment Calls

Ten final calls were evaluated across appointment scheduling, rescheduling, cancellation, medication refill handling, office information, insurance questions, ambiguity, preference correction, unusual scheduling requests, and conversation-state tracking.

The automated transcript-based evaluation identified **no confirmed product bugs in the final selected ten calls**.

The evaluator was deliberately conservative:
- it did not infer defects unsupported by the transcript,
- it did not classify transcription errors as product bugs,
- and it did not manufacture findings to increase bug count.

## Development Findings

Several issues were observed during development and informed improvements to the patient simulator. These development calls were not substituted for the final selected assessment recordings.

### 1. Patient speech could be interrupted mid-sentence

**Observed behavior:** Patient audio was occasionally cut off when remote speech detection triggered while generated speech was still playing.

**Impact:** Reduced conversational naturalness and could cause important information to be lost.

**Response:** Removed aggressive Twilio audio clearing and tuned turn-detection behavior.

### 2. Patient initially failed to correct incorrect identity information

**Observed behavior:** In an early call, an incorrectly repeated date of birth was not corrected. The patient also omitted the final letter while spelling "Morgan."

**Impact:** Identity-verification errors are particularly important in healthcare-style workflows.

**Response:** Added exact DOB, callback number, first/last-name spelling, and explicit correction behavior to every scenario.

### 3. Internal scenario instructions leaked into conversation

**Observed behavior:** The patient paraphrased an internal instruction by saying language similar to "rather than create a second appointment."

**Impact:** The caller sounded like a test harness rather than a real patient.

**Response:** Added explicit separation between silent behavior instructions and spoken patient language and simplified scenario prompts.

### 4. Generic acknowledgments did not always answer the latest question

**Observed behavior:** When asked a closing question such as whether anything else was needed, the patient sometimes responded with a generic acknowledgment such as "Okay, perfect."

**Impact:** Reduced conversational coherence.

**Response:** Added last-turn grounding rules requiring the patient to answer the most recent completed question directly.

### 5. Turn-taking required iterative tuning

**Observed behavior:** Different voice-activity-detection settings produced tradeoffs between delayed responses, overlap, and premature interruption.

**Impact:** Voice quality and natural turn-taking are core assessment requirements.

**Response:** Iteratively tuned Realtime turn detection and patient response instructions, then manually reviewed recordings before selecting the final set.

## Final Result

The final ten calls were selected only after the patient simulator consistently produced complete two-sided conversations with substantially improved identity consistency, turn-taking, response grounding, and scenario adherence.
