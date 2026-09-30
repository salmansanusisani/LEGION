"""Run one generic BAND seat backed by OpenCode Big Pickle."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from band import Agent, configure_logging
from band.adapters import OpencodeAdapter, OpencodeAdapterConfig
from band.config import load_agent_config
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SEATS = {"coordinator", "implementer", "verifier", "experience_reviewer"}


async def main() -> None:
    load_dotenv(ROOT / ".env")
    configure_logging(root_level="INFO")

    seat = os.environ.get("BAND_SEAT", "").strip()
    if seat not in SEATS:
        choices = ", ".join(sorted(SEATS))
        raise SystemExit(f"Set BAND_SEAT to one of: {choices}")

    mandate_path = ROOT / "mandates" / f"{seat}.md"
    mandate = mandate_path.read_text(encoding="utf-8")
    agent_id, api_key = load_agent_config(seat)

    autonomous = os.environ.get("BAND_AUTONOMOUS", "0") == "1"
    adapter = OpencodeAdapter(
        config=OpencodeAdapterConfig(
            base_url=os.environ.get("OPENCODE_BASE_URL", "http://127.0.0.1:4096"),
            directory=str(ROOT),
            provider_id="opencode",
            model_id="big-pickle",
            custom_section=mandate,
            include_base_instructions=True,
            approval_mode="auto_accept" if autonomous else "manual",
            question_mode="auto_reject" if autonomous else "manual",
            turn_timeout_s=900.0,
        )
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.environ.get(
            "BAND_WS_URL", "wss://app.band.ai/api/v1/socket/websocket"
        ),
        rest_url=os.environ.get("BAND_REST_URL", "https://app.band.ai"),
    )

    logging.getLogger(__name__).info(
        "Starting BAND seat=%s model=opencode/big-pickle autonomous=%s",
        seat,
        autonomous,
    )
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

