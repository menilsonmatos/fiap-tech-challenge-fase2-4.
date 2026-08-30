from __future__ import annotations

import argparse
import csv
from pathlib import Path


DATASET = "basedosdados.br_inep_avaliacao_alfabetizacao"
TABLES = {
    "municipio": "municipio",
    "uf": "uf",
    "meta_brasil": "meta_alfabetizacao_brasil",
    "meta_uf": "meta_alfabetizacao_uf",
    "meta_municipio": "meta_alfabetizacao_municipio",
    "alunos": "alunos",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai as fontes oficiais da Base dos Dados")
    parser.add_argument("--billing-project", required=True, help="Projeto GCP usado pelo BigQuery")
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--output", type=Path, default=Path("data/official"))
    args = parser.parse_args()

    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise SystemExit("Instale a dependência: pip install -e .[gcp]") from exc

    args.output.mkdir(parents=True, exist_ok=True)
    client = bigquery.Client(project=args.billing_project)
    for table_name in TABLES.values():
        selected_columns = "*"
        if table_name == "alunos":
            selected_columns = (
                "ano, id_municipio, id_escola, id_aluno, rede, presenca, "
                "preenchimento_caderno, alfabetizado, proficiencia, peso_aluno"
            )
        query = (
            f"SELECT {selected_columns} FROM `{DATASET}.{table_name}` "
            f"WHERE ano = {args.year}"
        )
        _write_query(client, query, args.output / f"{table_name}.csv")

    directory_query = f"""
        SELECT DISTINCT diretorio.id_municipio, diretorio.nome, diretorio.sigla_uf
        FROM `basedosdados.br_bd_diretorios_brasil.municipio` AS diretorio
        INNER JOIN `{DATASET}.municipio` AS indicador USING (id_municipio)
        WHERE indicador.ano = {args.year}
    """
    _write_query(client, directory_query, args.output / "diretorio_municipio.csv")


def _write_query(client: object, query: str, output: Path) -> None:
    rows = client.query(query).result()  # type: ignore[attr-defined]
    fields = [field.name for field in rows.schema]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row.items()))
    print(f"{output}: {rows.total_rows} registros")


if __name__ == "__main__":
    main()
