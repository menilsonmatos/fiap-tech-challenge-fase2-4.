from __future__ import annotations

import argparse
import csv
from pathlib import Path

from alfabetizacao_pipeline.official_sources import OFFICIAL_SOURCE_FILES


def main() -> None:
    parser = argparse.ArgumentParser(description="Envia os extratos oficiais para a Bronze no S3")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--source-dir", type=Path, default=Path("data/official"))
    args = parser.parse_args()

    import boto3

    for filename in OFFICIAL_SOURCE_FILES.values():
        source = args.source_dir / filename
        if not source.exists():
            raise FileNotFoundError(f"Fonte oficial ausente: {source}")
    with (args.source_dir / OFFICIAL_SOURCE_FILES["alunos"]).open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        fields = set(csv.DictReader(handle).fieldnames or [])
        if "total_avaliados" not in fields or fields & {"id_aluno", "id_escola"}:
            raise ValueError("Use o agregado de alunos sem identificadores individuais")
    s3 = boto3.client("s3")
    for filename in OFFICIAL_SOURCE_FILES.values():
        source = args.source_dir / filename
        key = f"bronze/oficial/{filename}"
        s3.upload_file(str(source), args.bucket, key)
        print(f"s3://{args.bucket}/{key}")
    manifest = args.source_dir / "extraction_manifest.json"
    if manifest.exists():
        s3.upload_file(str(manifest), args.bucket, "bronze/oficial/extraction_manifest.json")


if __name__ == "__main__":
    main()
