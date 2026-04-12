from pathlib import Path
import runpy
import sys


def main():
    here = Path(__file__).resolve()
    target = here.parents[2] / "iot" / "stdin_to_tcp.py"
    if not target.exists():
        raise FileNotFoundError(f"Forwarder script not found: {target}")
    sys.path.insert(0, str(target.parent.parent))
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
