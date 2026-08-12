from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import websockets
from fastapi import WebSocket, WebSocketDisconnect

from app.config import Settings
from app.scenarios import Scenario, get_scenario

log = logging.getLogger(__name__)


class RealtimeBridge:
    """
    Bridges Twilio bidirectional Media Streams to OpenAI Realtime.

    Twilio sends/accepts base64-encoded G.711 μ-law telephony audio.
    OpenAI Realtime is configured for audio/pcmu in both directions, so the
    payload can pass through without resampling or transcoding.
    """

    def __init__(self, twilio_ws: WebSocket, settings: Settings):
        self.twilio_ws = twilio_ws
        self.settings = settings

        self.scenario: Scenario | None = None
        self.stream_sid: str | None = None
        self.call_sid: str | None = None

    async def run(self) -> None:
        await self._wait_for_start_event()

        if self.scenario is None:
            raise RuntimeError(
                "Twilio stream started without a valid scenario."
            )

        model = self.settings.openai_realtime_model
        url = f"wss://api.openai.com/v1/realtime?model={model}"

        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "OpenAI-Safety-Identifier": (
                "pgai-authorized-assessment-patient-simulator"
            ),
        }

        log.info(
            "Connecting to OpenAI Realtime model=%s scenario=%s",
            model,
            self.scenario.id,
        )

        async with websockets.connect(
            url,
            additional_headers=headers,
            max_size=None,
            ping_interval=20,
            ping_timeout=20,
        ) as openai_ws:
            await openai_ws.send(
                json.dumps(self._session_update())
            )

            twilio_to_openai = asyncio.create_task(
                self._twilio_to_openai(openai_ws),
                name="twilio-to-openai",
            )

            openai_to_twilio = asyncio.create_task(
                self._openai_to_twilio(openai_ws),
                name="openai-to-twilio",
            )

            done, pending = await asyncio.wait(
                {twilio_to_openai, openai_to_twilio},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

            await asyncio.gather(
                *pending,
                return_exceptions=True,
            )

            for task in done:
                exc = task.exception()
                if exc:
                    raise exc

    async def _wait_for_start_event(self) -> None:
        """
        Wait for Twilio's stream-start event.

        Custom <Parameter> values are delivered inside
        start.customParameters.
        """
        try:
            while True:
                message = await self.twilio_ws.receive_text()
                data = json.loads(message)

                event = data.get("event")

                if event == "connected":
                    log.info(
                        "Twilio media websocket connected."
                    )
                    continue

                if event == "start":
                    start = data.get("start", {})

                    self.stream_sid = start.get("streamSid")
                    self.call_sid = start.get("callSid")

                    custom_parameters = start.get(
                        "customParameters",
                        {},
                    )

                    scenario_id = custom_parameters.get(
                        "scenario"
                    )

                    if not scenario_id:
                        raise RuntimeError(
                            "Missing Twilio custom parameter: scenario"
                        )

                    self.scenario = get_scenario(
                        scenario_id
                    )

                    log.info(
                        "Twilio stream started "
                        "stream_sid=%s call_sid=%s scenario=%s",
                        self.stream_sid,
                        self.call_sid,
                        scenario_id,
                    )

                    return

                if event == "stop":
                    raise RuntimeError(
                        "Twilio stream stopped before start event."
                    )

        except WebSocketDisconnect:
            raise RuntimeError(
                "Twilio websocket disconnected before stream start."
            ) from None

    def _session_update(self) -> dict[str, Any]:
        if self.scenario is None:
            raise RuntimeError(
                "Cannot configure Realtime session before "
                "scenario is loaded."
            )

        return {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "model": self.settings.openai_realtime_model,
                "output_modalities": ["audio"],
                "instructions": self.scenario.patient_prompt(),
                "audio": {
                    "input": {
                        "format": {
                            "type": "audio/pcmu",
                        },
                        "noise_reduction": None,
                        "turn_detection": {
                            "type": "semantic_vad",
                            "eagerness": "medium",
                            "create_response": True,
                            "interrupt_response": True,
                        },
                    },
                    "output": {
                        "format": {
                            "type": "audio/pcmu",
                        },
                        "voice": (
                            self.settings.openai_realtime_voice
                        ),
                        "speed": 1.0,
                    },
                },
                "reasoning": {
                    "effort": "none",
                },
                "max_output_tokens": 250,
            },
        }

    async def _twilio_to_openai(
        self,
        openai_ws,
    ) -> None:
        try:
            while True:
                message = await self.twilio_ws.receive_text()
                data = json.loads(message)

                event = data.get("event")

                if event == "media":
                    payload = data["media"]["payload"]

                    await openai_ws.send(
                        json.dumps(
                            {
                                "type": (
                                    "input_audio_buffer.append"
                                ),
                                "audio": payload,
                            }
                        )
                    )

                elif event == "stop":
                    log.info(
                        "Twilio stream stopped stream_sid=%s",
                        self.stream_sid,
                    )
                    return

        except WebSocketDisconnect:
            log.info(
                "Twilio websocket disconnected."
            )

        except asyncio.CancelledError:
            raise

    async def _openai_to_twilio(
        self,
        openai_ws,
    ) -> None:
        try:
            async for raw in openai_ws:
                event = json.loads(raw)
                event_type = event.get("type")

                if event_type == "response.output_audio.delta":
                    if not self.stream_sid:
                        continue

                    audio_b64 = event.get("delta")

                    if audio_b64:
                        await self.twilio_ws.send_text(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": self.stream_sid,
                                    "media": {
                                        "payload": audio_b64,
                                    },
                                }
                            )
                        )

                elif (
                    event_type
                    == "input_audio_buffer.speech_started"
                ):
                    # Let Realtime handle interruption server-side.
                    # Do not flush Twilio's playback buffer on every
                    # detected speech start because brief overlap/noise
                    # can otherwise cut the patient off mid-sentence.
                    log.debug(
                        "Remote speech detected."
                    )

                elif event_type == "error":
                    error = event.get(
                        "error",
                        {},
                    )

                    log.error(
                        "OpenAI Realtime error: %s",
                        error,
                    )

                elif event_type == "session.created":
                    log.info(
                        "OpenAI Realtime session created."
                    )

                elif event_type == "session.updated":
                    log.info(
                        "OpenAI Realtime session updated."
                    )

                elif event_type == "response.done":
                    log.debug(
                        "OpenAI response completed."
                    )

                elif (
                    event_type
                    == "input_audio_buffer.speech_stopped"
                ):
                    log.debug(
                        "Remote speech stopped."
                    )

        except asyncio.CancelledError:
            raise
