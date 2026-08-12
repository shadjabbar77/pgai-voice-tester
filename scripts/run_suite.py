from __future__ import annotations

import argparse
import time

from app.caller import make_call
from app.config import get_settings
from app.scenarios import load_scenarios


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run scenarios sequentially. Use only after Call #1 quality is validated."
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--gap-seconds",
        type=int,
        default=20,
        help="Gap between call initiations; does not wait for the previous call to finish.",
    )
    args = parser.parse_args()

    settings = get_settings()
    scenarios = list(load_scenarios().values())[: args.limit]

    for index, scenario in enumerate(scenarios, start=1):
        sid = make_call(settings, scenario)
        print(f"[{index}/{len(scenarios)}] {scenario.id}: {sid}")
        if index != len(scenarios):
            time.sleep(args.gap_seconds)


if __name__ == "__main__":
    main()
