"""Check external Markdown links with retries and distinguish hard failures from warnings."""

import argparse
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urldefrag

import httpx

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass(frozen=True, slots=True)
class LinkResult:
    """One normalized external link check."""

    url: str
    status: str
    detail: str


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--attempts", type=int, default=3)
    return parser.parse_args()


def external_links() -> list[str]:
    """Return unique HTTP(S) Markdown targets without fragments."""
    links = set()
    for path in ROOT.rglob("*.md"):
        if {".git", ".venv", ".foundry"} & set(path.parts):
            continue
        for target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
            url, _ = urldefrag(target.strip())
            if url.startswith(("https://", "http://")):
                links.add(url)
    return sorted(links)


def check_link(url: str, attempts: int) -> LinkResult:
    """Check one URL; only definitive missing-resource responses are hard failures."""
    headers = {"User-Agent": "foundry-bootcamp-link-check/1.0"}
    last_detail = "not checked"
    for attempt in range(attempts):
        try:
            with (
                httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client,
                client.stream("GET", url) as response,
            ):
                status_code = response.status_code
            if status_code < 400:
                return LinkResult(url, "pass", f"HTTP {status_code}")
            if status_code in {404, 410}:
                return LinkResult(url, "fail", f"HTTP {status_code}")
            last_detail = f"HTTP {status_code}"
        except httpx.HTTPError as exc:
            last_detail = f"{type(exc).__name__}: {exc}"
        if attempt + 1 < attempts:
            time.sleep(2**attempt)
    return LinkResult(url, "warn", last_detail)


def main() -> int:
    args = _arguments()
    links = external_links()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda url: check_link(url, args.attempts), links))

    for result in results:
        print(f"{result.status.upper():4}  {result.url}  {result.detail}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps([asdict(result) for result in results], indent=2),
            encoding="utf-8",
        )
    return 1 if any(result.status == "fail" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
