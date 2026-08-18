"""Run a command with the selected azd environment values without shell evaluation."""

import argparse
import json
import os
import shutil
import subprocess


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        parser.error("a command is required")
    return args


def main() -> int:
    args = _arguments()
    azd = shutil.which("azd")
    if not azd:
        print("Azure Developer CLI was not found on PATH.")
        return 1
    result = subprocess.run(  # noqa: S603 - azd is resolved to an absolute trusted executable.
        [azd, "env", "get-values", "--output", "json"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr.strip() or "Unable to read the selected azd environment.")
        return result.returncode

    values = json.loads(result.stdout)
    environment = os.environ.copy()
    environment.update({str(key): str(value) for key, value in values.items()})
    executable = shutil.which(args.command[0])
    if not executable:
        print(f"Command was not found on PATH: {args.command[0]}")
        return 1
    command = [executable, *args.command[1:]]
    completed = subprocess.run(  # noqa: S603 - argument list execution intentionally avoids a shell.
        command,
        env=environment,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
