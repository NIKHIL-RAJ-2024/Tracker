from pathlib import Path
import subprocess
import sys


def main() -> int:
    app_path = Path(__file__).with_name("tracker.py")
    result = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path)],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())