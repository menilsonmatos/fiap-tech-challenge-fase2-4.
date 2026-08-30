from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import IndicatorRecord
from .quality import QualityIssue


OFFICIAL_SOURCE_FILES = {
    "municipio": "municipio.csv",
    "uf": "uf.csv",
    "meta_brasil": "meta_alfabetizacao_brasil.csv",
    "meta_uf": "meta_alfabetizacao_uf.csv",
    "meta_municipio": "meta_alfabetizacao_municipio.csv",
    "alunos": "alunos.csv",
    "diretorio_municipio": "diretorio_municipio.csv",
}


@dataclass(frozen=True)
class OfficialIntegration:
    records: list[IndicatorRecord]
    issues: list[QualityIssue]
    source_rows: dict[str, int]


def read_source_rows(source_dir: Path) -> dict[str, list[dict[str, str]]]:
    sources: dict[str, list[dict[str, str]]] = {}
    missing: list[str] = []
    for name, filename in OFFICIAL_SOURCE_FILES.items():
        path = source_dir / filename
        if not path.exists():
            missing.append(filename)
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sources[name] = list(csv.DictReader(handle))
    if missing:
        raise FileNotFoundError("Fontes oficiais ausentes: " + ", ".join(sorted(missing)))
    return sources


def integrate_official_sources(
    sources: dict[str, list[dict[str, Any]]],
) -> OfficialIntegration:
    directories = {
        str(row["id_municipio"]): row for row in sources["diretorio_municipio"]
    }
    municipal_targets = _index(sources["meta_municipio"], "ano", "id_municipio")
    uf_results = _index_preferred_network(sources["uf"], "ano", "sigla_uf")
    uf_targets = _index_preferred_network(sources["meta_uf"], "ano", "sigla_uf")
    brazil_results = _index_preferred_network(sources["meta_brasil"], "ano")
    brazil_targets = brazil_results
    students = _student_counts(sources["alunos"])
    records: list[IndicatorRecord] = []
    issues: list[QualityIssue] = []

    for row in sources["municipio"]:
        if not _is_municipal(row.get("rede")):
            continue
        year = int(row["ano"])
        municipality_id = str(row["id_municipio"])
        key = f"{year}:{municipality_id}"
        directory = directories.get(municipality_id)
        target = municipal_targets.get((str(year), municipality_id))
        if directory is None:
            issues.append(
                QualityIssue(
                    "municipality_relationship",
                    "error",
                    key,
                    "Município sem dimensão no diretório",
                )
            )
            continue
        if target is None:
            issues.append(
                QualityIssue(
                    "municipal_target_relationship",
                    "error",
                    key,
                    "Município sem meta oficial",
                )
            )
            continue
        uf = str(directory["sigla_uf"]).upper()
        uf_result = uf_results.get((str(year), uf))
        uf_target = uf_targets.get((str(year), uf))
        brazil_result = brazil_results.get((str(year),))
        brazil_target = brazil_targets.get((str(year),))
        missing_relations = [
            name
            for name, value in (
                ("resultado_uf", uf_result),
                ("meta_uf", uf_target),
                ("resultado_brasil", brazil_result),
                ("meta_brasil", brazil_target),
            )
            if value is None
        ]
        if missing_relations:
            issues.append(
                QualityIssue(
                    "official_relationships",
                    "error",
                    key,
                    "Relações ausentes: " + ", ".join(missing_relations),
                )
            )
            continue
        records.append(
            IndicatorRecord(
                ano=year,
                sigla_uf=uf,
                id_municipio=municipality_id,
                nome_municipio=str(directory["nome"]),
                percentual_alfabetizado=_number(row["taxa_alfabetizacao"]),
                meta_percentual=_number(target["meta_alfabetizacao_2024"]),
                total_avaliados=students.get((str(year), municipality_id), 0),
                taxa_alfabetizacao_uf=_number(uf_result["taxa_alfabetizacao"]),
                meta_alfabetizacao_uf=_number(uf_target["meta_alfabetizacao_2024"]),
                taxa_alfabetizacao_brasil=_number(brazil_result["taxa_alfabetizacao"]),
                meta_alfabetizacao_brasil=_number(brazil_target["meta_alfabetizacao_2024"]),
                percentual_participacao=_optional_number(target.get("percentual_participacao")),
                fonte="INEP / Base dos Dados - br_inep_avaliacao_alfabetizacao",
            )
        )
    return OfficialIntegration(
        records=records,
        issues=issues,
        source_rows={name: len(rows) for name, rows in sources.items()},
    )


def _index(rows: list[dict[str, Any]], *columns: str) -> dict[tuple[str, ...], dict[str, Any]]:
    return {tuple(str(row[column]) for column in columns): row for row in rows}


def _index_preferred_network(
    rows: list[dict[str, Any]], *columns: str
) -> dict[tuple[str, ...], dict[str, Any]]:
    result: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(str(row[column]) for column in columns)
        current = result.get(key)
        if current is None or _network_priority(row.get("rede")) > _network_priority(
            current.get("rede")
        ):
            result[key] = row
    return result


def _student_counts(rows: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    students: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        if str(row.get("alfabetizado", "")).strip() == "":
            continue
        key = (str(row["ano"]), str(row["id_municipio"]))
        students.setdefault(key, set()).add(str(row["id_aluno"]))
    return {key: len(ids) for key, ids in students.items()}


def _is_municipal(value: Any) -> bool:
    return "municip" in str(value or "").strip().lower()


def _network_priority(value: Any) -> int:
    normalized = str(value or "").strip().lower()
    if "públic" in normalized or "public" in normalized:
        return 3
    if "municip" in normalized:
        return 2
    return 1


def _number(value: Any) -> float:
    return float(str(value).replace(",", "."))


def _optional_number(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return _number(value)
