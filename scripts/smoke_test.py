"""Smoke-test health and one grounded streaming response."""

import argparse
import os

import httpx

from support_assistant.evaluation.local import invoke_chat


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("SERVICE_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.getenv("BOOTCAMP_ACCESS_TOKEN"))
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if not args.token:
        raise SystemExit("Set BOOTCAMP_ACCESS_TOKEN or pass --token")

    with httpx.Client(timeout=60.0) as client:
        health = client.get(f"{args.base_url.rstrip('/')}/health")
        health.raise_for_status()
        result = invoke_chat(
            client,
            base_url=args.base_url,
            token=args.token,
            query="Does the warranty cover accidental damage?",
        )

    citation_ids = {citation.id for citation in result.citations}
    if "warranty-policy" not in citation_ids:
        print("FAIL  grounded chat did not cite warranty-policy")
        return 1
    if "does not cover accidental damage" not in result.response.casefold():
        print("FAIL  grounded chat did not return the expected warranty exclusion")
        return 1

    print("PASS  health endpoint and grounded chat response")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
