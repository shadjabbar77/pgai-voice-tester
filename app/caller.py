from __future__ import annotations

import json
from datetime import datetime, timezone

from twilio.rest import Client

from app.config import ASSESSMENT_NUMBER, CALLS_DIR, Settings, validate_destination
from app.scenarios import Scenario


def make_call(settings: Settings, scenario: Scenario) -> str:
    destination = ASSESSMENT_NUMBER
    validate_destination(destination)

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    base = settings.public_https_url

    call = client.calls.create(
        to=destination,
        from_=settings.twilio_phone_number,
        url=f"{base}/twilio/voice?scenario={scenario.id}",
        method="POST",
        record=True,
        recording_channels="dual",
        recording_status_callback=f"{base}/twilio/recording",
        recording_status_callback_method="POST",
        recording_status_callback_event=["completed"],
        status_callback=f"{base}/twilio/status",
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        timeout=30,
    )

    call_dir = CALLS_DIR / call.sid
    call_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "scenario_id": scenario.id,
        "scenario_title": scenario.title,
        "call_sid": call.sid,
        "destination": destination,
        "originating_number": settings.twilio_phone_number,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (call_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (call_dir / "scenario.json").write_text(json.dumps({
        "id": scenario.id,
        "title": scenario.title,
        "objective": scenario.objective,
        "persona": scenario.persona,
        "facts": scenario.facts,
        "behaviors": scenario.behaviors,
        "success_condition": scenario.success_condition,
        "risk_focus": scenario.risk_focus,
    }, indent=2))

    return call.sid
