from __future__ import annotations

import base64
import csv
import io
import json
import os
from datetime import datetime, timezone
from typing import Any

from .contracts import parse_event, parse_record
from .quality import validate_dataset
from .official_sources import OFFICIAL_SOURCE_FILES, integrate_official_sources
from .transforms import aggregate_by_uf, deduplicate, vulnerability_ranking


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    if not rows:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def transform_csv(content: bytes) -> dict[str, bytes | dict[str, Any]]:
    text = content.decode("utf-8-sig")
    records = [parse_record(row) for row in csv.DictReader(io.StringIO(text))]
    issues = validate_dataset(records)
    invalid_keys = {issue.key for issue in issues if issue.severity == "error"}
    valid = deduplicate(
        [record for record in records if f"{record.ano}:{record.id_municipio}" not in invalid_keys]
    )
    silver = [record.to_dict() for record in valid]
    manifest = {
        "input_rows": len(records),
        "silver_rows": len(valid),
        "quality_errors": sum(issue.severity == "error" for issue in issues),
        "quality_warnings": sum(issue.severity == "warning" for issue in issues),
        "status": "success" if not invalid_keys else "success_with_quarantine",
    }
    return {
        "silver": _csv_bytes(silver),
        "gold_uf": _csv_bytes(aggregate_by_uf(valid)),
        "gold_ranking": _csv_bytes(vulnerability_ranking(valid)),
        "quality": (
            "\n".join(json.dumps(issue.__dict__, ensure_ascii=False) for issue in issues)
        ).encode(),
        "manifest": manifest,
    }


def transform_official_csvs(
    contents: dict[str, bytes],
) -> dict[str, bytes | dict[str, Any]]:
    sources = {
        name: list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
        for name, content in contents.items()
    }
    integration = integrate_official_sources(sources)
    issues = [*integration.issues, *validate_dataset(integration.records)]
    invalid_keys = {issue.key for issue in issues if issue.severity == "error"}
    valid = deduplicate(
        [
            record
            for record in integration.records
            if f"{record.ano}:{record.id_municipio}" not in invalid_keys
        ]
    )
    manifest = {
        "source": "Base dos Dados / INEP - br_inep_avaliacao_alfabetizacao",
        "source_rows": integration.source_rows,
        "integrated_rows": len(integration.records),
        "silver_rows": len(valid),
        "quality_errors": sum(issue.severity == "error" for issue in issues),
        "quality_warnings": sum(issue.severity == "warning" for issue in issues),
        "status": "success" if not invalid_keys else "success_with_quarantine",
    }
    return {
        "silver": _csv_bytes([record.to_dict() for record in valid]),
        "gold_uf": _csv_bytes(aggregate_by_uf(valid)),
        "gold_ranking": _csv_bytes(vulnerability_ranking(valid)),
        "quality": (
            "\n".join(json.dumps(issue.__dict__, ensure_ascii=False) for issue in issues)
        ).encode(),
        "manifest": manifest,
    }


def batch_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    import boto3

    bucket = event.get("bucket") or os.environ["DATA_BUCKET"]
    s3 = boto3.client("s3")
    if event.get("mode", "official") == "official":
        source_keys = event.get("source_keys") or {
            name: f"bronze/oficial/{filename}"
            for name, filename in OFFICIAL_SOURCE_FILES.items()
        }
        contents = {
            name: s3.get_object(Bucket=bucket, Key=key)["Body"].read()
            for name, key in source_keys.items()
        }
        transformed = transform_official_csvs(contents)
    else:
        source_key = event.get("source_key", "bronze/indicador_alfabetizacao.csv")
        transformed = transform_csv(s3.get_object(Bucket=bucket, Key=source_key)["Body"].read())
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outputs = {
        "silver/indicadores.csv": transformed["silver"],
        "gold/indicadores_uf/data.csv": transformed["gold_uf"],
        "gold/ranking_vulnerabilidade/data.csv": transformed["gold_ranking"],
        f"quarantine/quality_issues_{run_id}.jsonl": transformed["quality"],
        f"manifests/{run_id}.json": json.dumps(
            transformed["manifest"], ensure_ascii=False
        ).encode(),
    }
    for key, body in outputs.items():
        s3.put_object(Bucket=bucket, Key=key, Body=body)
    return {**transformed["manifest"], "bucket": bucket, "run_id": run_id}


def streaming_handler(event: dict[str, Any], _context: Any) -> dict[str, int]:
    import boto3

    bucket = os.environ["DATA_BUCKET"]
    s3 = boto3.client("s3")
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in event.get("Records", []):
        try:
            payload = json.loads(base64.b64decode(item["kinesis"]["data"]))
            accepted.append(parse_event(payload).to_dict())
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            rejected.append({"error": str(exc), "record": item})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    if accepted:
        s3.put_object(
            Bucket=bucket,
            Key=f"silver/stream/year={datetime.now(timezone.utc).year}/{stamp}.jsonl",
            Body=("\n".join(json.dumps(row, ensure_ascii=False) for row in accepted)).encode(),
        )
    if rejected:
        s3.put_object(
            Bucket=bucket,
            Key=f"quarantine/stream/{stamp}.jsonl",
            Body=("\n".join(json.dumps(row, ensure_ascii=False) for row in rejected)).encode(),
        )
    return {"accepted": len(accepted), "rejected": len(rejected)}
