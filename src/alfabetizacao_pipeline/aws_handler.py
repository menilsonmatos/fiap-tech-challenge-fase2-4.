from __future__ import annotations

import base64
import csv
import io
import json
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from typing import Any

from .contracts import parse_event, parse_record
from .quality import validate_dataset, validate_record
from .official_sources import OFFICIAL_SOURCE_FILES, integrate_official_sources, read_source_rows
from .snapshots import RAW_FILES, file_hash, validate_snapshot
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
        "municipal_input_rows": integration.municipal_input_rows,
        "municipal_excluded_rows": integration.municipal_input_rows - len(valid),
        "students_mode": "aggregate_at_source_no_individual_identifiers",
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
    source_pointer = None
    if event.get("mode", "official") == "official":
        source_pointer = event.get("snapshot") or json.loads(
            s3.get_object(Bucket=bucket, Key="control/latest_official.json")["Body"].read())
        prefix = source_pointer["prefix"]
        if not re.fullmatch(r"bronze/oficial/ingestao=[a-f0-9]{32}", prefix):
            raise ValueError("Prefixo de snapshot inválido")
        with tempfile.TemporaryDirectory(prefix="fiap-batch-") as directory:
            source = Path(directory)
            for name in (*RAW_FILES, "extraction_manifest.json"):
                s3.download_file(bucket, f"{prefix}/{name}", str(source / name))
            if file_hash(source / "extraction_manifest.json") != source_pointer["manifest_sha256"]:
                raise ValueError("Manifesto do snapshot divergente")
            validate_snapshot(source)
            sources = read_source_rows(source)
            transformed = transform_official_csvs({name: _csv_bytes(rows) for name, rows in sources.items()})
            transformed["manifest"]["students_mode"] = "raw_bronze_aggregate_in_silver"
            transformed["manifest"]["source_rows"]["alunos"] = sum(int(r["registros_origem"]) for r in sources["alunos"])
            transformed["manifest"]["student_aggregate_rows"] = len(sources["alunos"])
            transformed["manifest"]["snapshot"] = source_pointer
    else:
        source_key = event.get("source_key", "bronze/indicador_alfabetizacao.csv")
        transformed = transform_csv(s3.get_object(Bucket=bucket, Key=source_key)["Body"].read())
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex
    transformed["manifest"]["run_id"] = run_id
    if transformed["manifest"]["silver_rows"] == 0:
        s3.put_object(Bucket=bucket, Key=f"quarantine/quality_issues_{run_id}.jsonl", Body=transformed["quality"])
        raise ValueError("Nenhum município aprovado; Gold anterior preservada")
    outputs = {
        "silver/indicadores.csv": transformed["silver"],
        "gold/indicadores_uf/data.csv": transformed["gold_uf"],
        "gold/ranking_vulnerabilidade/data.csv": transformed["gold_ranking"],
        f"quarantine/quality_issues_{run_id}.jsonl": transformed["quality"],
        f"manifests/{run_id}.json": json.dumps(
            transformed["manifest"], ensure_ascii=False
        ).encode(),
    }
    # Histórico do resultado por execução; os caminhos atuais abaixo são apenas projeções.
    for key, body in outputs.items():
        s3.put_object(Bucket=bucket, Key=f"runs/{run_id}/{key}", Body=body)
    for key, body in outputs.items():
        s3.put_object(Bucket=bucket, Key=key, Body=body)
    return {**transformed["manifest"], "bucket": bucket, "run_id": run_id}


def streaming_handler(event: dict[str, Any], _context: Any) -> dict[str, int]:
    import boto3

    bucket = os.environ["DATA_BUCKET"]
    s3 = boto3.client("s3")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex
    # Persistir o envelope original (incluindo base64 e metadados) antes de tratar.
    s3.put_object(Bucket=bucket, Key=f"bronze/stream/ingestao={stamp}/event.json",
                  Body=json.dumps(event, ensure_ascii=False).encode())
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in event.get("Records", []):
        try:
            payload = json.loads(base64.b64decode(item["kinesis"]["data"]))
            if not isinstance(payload, dict):
                raise ValueError("Evento precisa ser um objeto JSON")
            record = parse_event(payload)
            errors = [issue for issue in validate_record(record) if issue.severity == "error"]
            if errors:
                raise ValueError("; ".join(issue.rule for issue in errors))
            accepted.append(record.to_dict())
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            rejected.append({"error": str(exc), "record": item})
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
