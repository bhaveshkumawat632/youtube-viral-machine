#!/usr/bin/env python3
"""Production entrypoint.

Default behavior is strict: do not render unless real production assets are
present and pass the quality contract. Use `--readiness-demo` only for a local
style prototype; it is not a channel upload candidate.
"""

from __future__ import annotations

import argparse

from production_gate import GateError, validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a production-grade Short.")
    parser.add_argument(
        "--readiness-demo",
        action="store_true",
        help="Render the local aghori-style prototype instead of a production video.",
    )
    args = parser.parse_args()

    if args.readiness_demo:
        from aghori_style_engine import main as demo_main

        return demo_main([])

    try:
        validate_manifest()
    except GateError as exc:
        print(exc)
        print()
        print("No video rendered. Add real assets in production_inputs/ first.")
        return 2

    from production_assembler import main as assemble_main

    return assemble_main()


if __name__ == "__main__":
    raise SystemExit(main())
