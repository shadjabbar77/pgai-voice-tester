from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx
from fastapi import FastAPI, Form, Response, WebSocket
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Connect, VoiceResponse

from app.config import CALLS_DIR, get_settings
from app.realtime_bridge import RealtimeBridge
from app.scenarios import get_scenario


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Pretty Good AI Patient Simulator")

settings = get_settings()
validator = RequestValidator(settings.twilio_auth_token)


def _call_dir(call_sid: str) -> Path:
    path = CALLS_DIR / call_sid
    path.mkdir(parents=True, exist_ok=True)
    return path


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "assessment_destination": "+18054398008",
        "realtime_model": settings.openai_realtime_model,
    }


@app.api_route("/twilio/voice", methods=["GET", "POST"])
async def twilio_voice(scenario: str):
    # Validate the requested scenario before returning TwiML.
    get_scenario(scenario)

    response = VoiceResponse()
    connect = Connect()

    stream = connect.stream(
        url=f"{settings.public_wss_url}/twilio/media"
    )

    # Twilio Media Streams do not support query parameters in the
    # WebSocket URL. Pass the scenario as a custom Stream parameter.
    stream.parameter(
        name="scenario",
        value=scenario,
    )

    response.append(connect)

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@app.websocket("/twilio/media")
async def twilio_media(websocket: WebSocket):
    await websocket.accept()

    bridge = RealtimeBridge(
        websocket,
        settings,
    )

    try:
        await bridge.run()

    except Exception:
        log.exception("Media bridge failed.")

        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@app.post("/twilio/status")
async def twilio_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
):
    path = _call_dir(CallSid) / "status.json"

    current = {}

    if path.exists():
        current = json.loads(path.read_text())

    current.update(
        {
            "call_sid": CallSid,
            "call_status": CallStatus,
        }
    )

    path.write_text(
        json.dumps(current, indent=2)
    )

    return {"ok": True}


@app.post("/twilio/recording")
async def twilio_recording(
    CallSid: str = Form(...),
    RecordingSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingStatus: str = Form(...),
    RecordingDuration: str = Form("0"),
):
    """
    Recording callback.

    Downloads the Twilio recording only after Twilio reports that
    processing has completed.
    """

    call_dir = _call_dir(CallSid)

    metadata = {
        "call_sid": CallSid,
        "recording_sid": RecordingSid,
        "recording_status": RecordingStatus,
        "recording_duration_seconds": int(
            RecordingDuration or 0
        ),
    }

    (call_dir / "recording.json").write_text(
        json.dumps(metadata, indent=2)
    )

    if RecordingStatus != "completed":
        return {
            "ok": True,
            "downloaded": False,
        }

    media_url = (
        RecordingUrl
        + ".mp3?RequestedChannels=2"
    )

    async with httpx.AsyncClient(
        auth=(
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        ),
        timeout=60.0,
        follow_redirects=True,
    ) as client:

        result = await client.get(media_url)

        if result.status_code >= 400:
            fallback = (
                RecordingUrl
                + ".mp3?RequestedChannels=1"
            )

            result = await client.get(fallback)

        result.raise_for_status()

    out = call_dir / "recording.mp3"
    out.write_bytes(result.content)

    log.info(
        "Saved recording %s",
        out,
    )

    return {
        "ok": True,
        "downloaded": True,
        "path": str(out),
    }