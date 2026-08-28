from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_local import read_csv
from .local_pipeline import run_batch, simulate_stream
from .quality import validate_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline de alfabetização")
    sub = parser.add_subparsers(dest="command", required=True)
    batch = sub.add_parser("batch", help="Executa o pipeline batch local")
    batch.add_argument("--source", type=Path, required=True)
    batch.add_argument("--output", type=Path, default=Path("data"))
    stream = sub.add_parser("simulate-stream", help="Simula eventos de streaming")
    stream.add_argument("--events", type=Path, required=True)
    stream.add_argument("--output", type=Path, default=Path("data"))
    validate = sub.add_parser("validate", help="Valida um CSV no contrato Silver")
    validate.add_argument("--input", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "batch":
        result = run_batch(args.source, args.output)
    elif args.command == "simulate-stream":
        result = simulate_stream(args.events, args.output)
    else:
        issues = validate_dataset(read_csv(args.input))
        result = {"issues": [issue.__dict__ for issue in issues], "valid": not issues}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

