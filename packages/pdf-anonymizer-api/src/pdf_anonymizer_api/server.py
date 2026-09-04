"""Process entry point. Does not import the CLI."""

from __future__ import annotations

import argparse

from pdf_anonymizer_api.app import create_app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Local HTTP service for pdf-anonymizer-core. "
            "No authentication. Default bind is this machine only."
        )
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="TCP port (default 8000).",
    )
    args = parser.parse_args(argv)
    import uvicorn

    uvicorn.run(create_app(), host=args.host, port=args.port)
