from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica eventos de demonstração no Kinesis")
    parser.add_argument("--stream", required=True)
    parser.add_argument("--file", type=Path, default=Path("data/source/eventos_indicadores.jsonl"))
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    import boto3

    client = boto3.client("kinesis")
    for line in args.file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        result = client.put_record(
            StreamName=args.stream,
            PartitionKey=payload["payload"]["id_municipio"],
            Data=json.dumps(payload).encode("utf-8"),
        )
        print(f"Publicado {payload['event_id']}: {result['SequenceNumber']}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
