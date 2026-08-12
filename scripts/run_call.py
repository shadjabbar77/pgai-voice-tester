from __future__ import annotations

import argparse

from app.caller import make_call
from app.config import ASSESSMENT_NUMBER, get_settings
from app.scenarios import get_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Place one authorized assessment call.")
    parser.add_argument("--scenario", required=True, help="Scenario ID from scenarios/scenarios.json")
    args = parser.parse_args()

    settings = get_settings()
    scenario = get_scenario(args.scenario)

    print(f"Scenario: {scenario.id} — {scenario.title}")
    print(f"Destination lock: {ASSESSMENT_NUMBER}")
    print(f"Originating number: {settings.twilio_phone_number}")

    sid = make_call(settings, scenario)
    print(f"Call started: {sid}")
    print(f"Artifacts will be stored under calls/{sid}/")


if __name__ == "__main__":
    main()
