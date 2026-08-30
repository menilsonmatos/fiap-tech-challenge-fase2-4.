from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from alfabetizacao_pipeline.official_queries import extraction_queries


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai as fontes oficiais da Base dos Dados")
    parser.add_argument("--billing-project", required=True, help="Projeto GCP usado pelo BigQuery")
    parser.add_argument("--year", type=int, choices=[2024], default=2024)
    parser.add_argument("--output", type=Path, default=Path("data/official"))
    parser.add_argument("--execute", action="store_true", help="Executa após estimar todas as consultas")
    parser.add_argument("--maximum-bytes-billed", type=int, default=1073741824)
    args = parser.parse_args()

    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise SystemExit("Instale a dependência: pip install -e .[gcp]") from exc

    client = bigquery.Client(project=args.billing_project)
    queries = extraction_queries(args.year)
    estimates = {}
    for name, query in queries.items():
        job = client.query(
            query, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        )
        estimates[name] = job.total_bytes_processed
        print(f"{name}: estimativa de {job.total_bytes_processed} bytes")
        if job.total_bytes_processed > args.maximum_bytes_billed:
            raise SystemExit(f"{name} excede o limite por consulta; nenhuma extração foi iniciada")
    print(f"Total estimado: {sum(estimates.values())} bytes")
    if not args.execute:
        print("Somente estimativa. Revise os volumes e acrescente --execute para extrair.")
        return

    # Não misturar novos extratos com arquivos antigos ou uma extração parcial.
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit("Diretório de saída não vazio; escolha outro --output")
    args.output.mkdir(parents=True, exist_ok=True)
    config = bigquery.QueryJobConfig(maximum_bytes_billed=args.maximum_bytes_billed)
    manifest = {
        "source": "basedosdados.br_inep_avaliacao_alfabetizacao",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "year": args.year,
        "students_mode": "aggregate_at_source_no_individual_identifiers",
        "files": {},
    }
    for name, query in queries.items():
        manifest["files"][name] = _write_query(
            client, query, args.output / f"{name}.csv", config
        )
    (args.output / "extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _write_query(client: object, query: str, output: Path, config: object) -> dict:
    job = client.query(query, job_config=config)  # type: ignore[attr-defined]
    rows = job.result()
    fields = [field.name for field in rows.schema]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row.items()))
    print(f"{output}: {rows.total_rows} registros")
    return {
        "filename": output.name,
        "rows": rows.total_rows,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "query": query,
        "job_id": job.job_id,
        "bytes_processed": job.total_bytes_processed,
    }


if __name__ == "__main__":
    main()
