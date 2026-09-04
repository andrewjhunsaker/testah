"""Serve the Current Snapshot dashboard on loopback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dashboard.server import make_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Current Snapshot dashboard.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to inspect")
    parser.add_argument("--port", type=int, default=0, help="Loopback port (0 selects one)")
    command_arguments = sys.argv[1:]
    args = parser.parse_args(command_arguments[1:] if command_arguments[:1] == ["--"] else command_arguments)

    server = make_server(args.root, args.port)
    host, port = server.server_address
    print(f"Dashboard listening at http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
