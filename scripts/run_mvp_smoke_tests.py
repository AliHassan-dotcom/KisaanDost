"""Run the MVP security smoke tests and report results.

Usage:
    python scripts/run_mvp_smoke_tests.py

The script executes pytest against tests/test_mvp.py and prints a concise
pass/fail summary. It exits with the pytest return code so CI can treat
failures as a build break.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_mvp.py",
        "-q",
        "--tb=short",
    ]
    print("Running MVP smoke tests...")
    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=project_root)
    if result.returncode == 0:
        print("\nMVP smoke tests PASSED.")
    else:
        print(f"\nMVP smoke tests FAILED with exit code {result.returncode}.")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
