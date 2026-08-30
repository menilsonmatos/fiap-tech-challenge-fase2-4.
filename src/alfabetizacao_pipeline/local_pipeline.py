from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import IndicatorRecord, parse_event
from .io_local import read_csv, read_jsonl, write_csv, write_jsonl
from .quality import validate_dataset
from .official_sources import OFFICIAL_SOURCE_FILES, integrate_official_sources, read_source_rows
from .transforms import aggregate_by_uf, deduplicate, vulnerability_ranking


def run_batch(source: Path, output: Path) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bronze_path = output / "bronze" / f"ingestao={run_id}" / source.name
    bronze_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, bronze_path)

    parsed = read_csv(bronze_path)
    issues = validate_dataset(parsed)
    invalid_keys = {issue.key for issue in issues if issue.severity == "error"}
    valid = [r for r in parsed if f"{r.ano}:{r.id_municipio}" not in invalid_keys]
    valid = deduplicate(valid)

    write_csv(output / "silver" / "indicadores.csv", [r.to_dict() for r in valid])
    write_jsonl(output / "quarantine" / "quality_issues.jsonl", (asdict(i) for i in issues))
    write_csv(output / "gold" / "indicadores_uf.csv", aggregate_by_uf(valid))
    write_csv(output / "gold" / "ranking_vulnerabilidade.csv", vulnerability_ranking(valid))

    manifest = {
        "run_id": run_id,
        "source": str(source),
        "bronze_object": str(bronze_path),
        "input_rows": len(parsed),
        "silver_rows": len(valid),
        "quality_errors": sum(i.severity == "error" for i in issues),
        "quality_warnings": sum(i.severity == "warning" for i in issues),
        "status": "success" if not invalid_keys else "success_with_quarantine",
    }
    manifest_path = output / "manifests" / f"{run_id}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def run_official_batch(source_dir: Path, output: Path) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bronze_dir = output / "bronze" / "oficial" / f"ingestao={run_id}"
    bronze_dir.mkdir(parents=True, exist_ok=True)
    for filename in OFFICIAL_SOURCE_FILES.values():
        shutil.copy2(source_dir / filename, bronze_dir / filename)

    integration = integrate_official_sources(read_source_rows(bronze_dir))
    issues = [*integration.issues, *validate_dataset(integration.records)]
    invalid_keys = {issue.key for issue in issues if issue.severity == "error"}
    valid = [
        record
        for record in deduplicate(integration.records)
        if f"{record.ano}:{record.id_municipio}" not in invalid_keys
    ]
    write_csv(output / "silver" / "indicadores_oficiais.csv", [r.to_dict() for r in valid])
    write_jsonl(
        output / "quarantine" / "official_quality_issues.jsonl",
        (asdict(i) for i in issues),
    )
    write_csv(output / "gold" / "indicadores_uf.csv", aggregate_by_uf(valid))
    write_csv(output / "gold" / "ranking_vulnerabilidade.csv", vulnerability_ranking(valid))
    manifest = {
        "run_id": run_id,
        "source": "Base dos Dados / INEP - br_inep_avaliacao_alfabetizacao",
        "bronze_prefix": str(bronze_dir),
        "source_rows": integration.source_rows,
        "integrated_rows": len(integration.records),
        "silver_rows": len(valid),
        "quality_errors": sum(i.severity == "error" for i in issues),
        "quality_warnings": sum(i.severity == "warning" for i in issues),
        "status": "success" if not invalid_keys else "success_with_quarantine",
    }
    manifest_path = output / "manifests" / f"{run_id}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def simulate_stream(events_path: Path, output: Path) -> dict[str, Any]:
    accepted: list[IndicatorRecord] = []
    rejected: list[dict[str, Any]] = []
    for event in read_jsonl(events_path):
        try:
            accepted.append(parse_event(event))
        except (TypeError, ValueError) as exc:
            rejected.append({"event": event, "error": str(exc)})

    write_jsonl(output / "bronze" / "stream" / "events.jsonl", read_jsonl(events_path))
    write_jsonl(output / "silver" / "stream_updates.jsonl", (r.to_dict() for r in accepted))
    write_jsonl(output / "quarantine" / "stream_rejected.jsonl", rejected)
    return {"accepted": len(accepted), "rejected": len(rejected)}
