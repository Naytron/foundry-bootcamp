"""Run azd deploy with bounded retry for newly propagated ACR authorization."""

import argparse
import shutil
import subprocess
import time

ACR_CONTEXT_MARKERS = (
    ".azurecr.io",
    "acrpull",
    "container registry",
    "failed to pull",
    "image pull",
    "imagepull",
    "pull access",
)
AUTHORIZATION_MARKERS = (
    "401",
    "403",
    "authentication required",
    "authorization",
    "denied",
    "forbidden",
    "unauthorized",
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempts", type=int, default=7)
    parser.add_argument("--initial-delay", type=float, default=5.0)
    args = parser.parse_args()
    if args.attempts < 1:
        parser.error("--attempts must be at least 1")
    if args.initial_delay < 0:
        parser.error("--initial-delay cannot be negative")
    return args


def _is_transient_acr_failure(output: str) -> bool:
    normalized = output.casefold()
    has_acr_context = any(marker in normalized for marker in ACR_CONTEXT_MARKERS)
    has_authorization_failure = any(marker in normalized for marker in AUTHORIZATION_MARKERS)
    return has_acr_context and has_authorization_failure


def main() -> int:
    """Retry only image-pull failures consistent with fresh AcrPull propagation."""
    args = _arguments()
    azd = shutil.which("azd")
    if not azd:
        print("Azure Developer CLI was not found on PATH.")
        return 1

    for attempt in range(args.attempts):
        result = subprocess.run(  # noqa: S603 - azd is resolved to an absolute executable.
            [azd, "deploy", "--no-prompt"],
            capture_output=True,
            check=False,
            text=True,
        )
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        print(output, flush=True)
        if result.returncode == 0:
            return 0
        if attempt + 1 >= args.attempts or not _is_transient_acr_failure(output):
            return result.returncode

        delay = min(args.initial_delay * (2**attempt), 60.0)
        print(
            f"ACR authorization may still be propagating; retrying in {delay:g} seconds.",
            flush=True,
        )
        time.sleep(delay)

    raise AssertionError("retry loop must return")


if __name__ == "__main__":
    raise SystemExit(main())
