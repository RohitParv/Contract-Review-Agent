"""Local CLI smoke test — talks to the orchestrator directly, no server
needed. Mirrors the original repo's local/run_a2a_local.py role.

Usage:
    cd contract-review-agent
    python local/run_local.py
    python local/run_local.py --contract samples/sample_lease.txt
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from orchestrator import Orchestrator  # noqa: E402
from tools.contract_extract import load_contract_text  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract", help="Path to a .pdf or .txt contract to load first"
    )
    parser.add_argument(
        "--message",
        default="What can you help me with?",
        help="First message to send (default: capability question)",
    )
    args = parser.parse_args()

    orchestrator = Orchestrator()
    session_id = str(uuid.uuid4())

    contract_text = load_contract_text(args.contract) if args.contract else None
    reply = orchestrator.run(
        args.message, session_id=session_id, contract_path_text=contract_text
    )
    print(f"\n--- session {session_id} ---")
    print(reply)

    print("\nType more messages (Ctrl+C to quit):")
    try:
        while True:
            user_input = input("> ")
            reply = orchestrator.run(user_input, session_id=session_id)
            print(reply)
    except (KeyboardInterrupt, EOFError):
        print("\nbye")


if __name__ == "__main__":
    main()
