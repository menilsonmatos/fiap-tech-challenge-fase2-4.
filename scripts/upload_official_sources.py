"""Publica um snapshot privado completo antes de atualizar seu ponteiro de leitura."""
import argparse
import json
from pathlib import Path
from uuid import uuid4

from alfabetizacao_pipeline.snapshots import RAW_FILES, file_hash, validate_snapshot


def upload_snapshot(s3, bucket, source):
    validate_snapshot(source)
    prefix = f"bronze/oficial/ingestao={uuid4().hex}"
    for name in (*RAW_FILES, "extraction_manifest.json"):
        s3.upload_file(str(source / name), bucket, f"{prefix}/{name}",
                       ExtraArgs={"ServerSideEncryption": "AES256"})
    pointer = {"prefix": prefix,
               "manifest_sha256": file_hash(source / "extraction_manifest.json")}
    s3.put_object(Bucket=bucket, Key="control/latest_official.json",
                  Body=json.dumps(pointer).encode(), ContentType="application/json")
    return pointer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--source-dir", type=Path, default=Path("data/official-raw"))
    args = parser.parse_args()
    import boto3
    print(json.dumps(upload_snapshot(boto3.client("s3"), args.bucket, args.source_dir), indent=2))


if __name__ == "__main__":
    main()
