from __future__ import annotations

import argparse
from pathlib import Path

from alfabetizacao_pipeline.official_sources import OFFICIAL_SOURCE_FILES


def main() -> None:
    parser = argparse.ArgumentParser(description="Envia os extratos oficiais para a Bronze no S3")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--source-dir", type=Path, default=Path("data/official"))
    args = parser.parse_args()

    import boto3

    s3 = boto3.client("s3")
    for filename in OFFICIAL_SOURCE_FILES.values():
        source = args.source_dir / filename
        if not source.exists():
            raise FileNotFoundError(f"Fonte oficial ausente: {source}")
        key = f"bronze/oficial/{filename}"
        s3.upload_file(str(source), args.bucket, key)
        print(f"s3://{args.bucket}/{key}")


if __name__ == "__main__":
    main()
