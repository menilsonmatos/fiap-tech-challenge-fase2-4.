from __future__ import annotations

import csv
import math
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
    "alunos": "alunos_agregados.csv",
    "diretorio_municipio": "diretorio_municipio.csv",
}


@dataclass(frozen=True)
class OfficialIntegration:
    records: list[IndicatorRecord]
    issues: list[QualityIssue]
    source_rows: dict[str, int]
    municipal_input_rows: int


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
    municipal_rows = _network_rows(sources["municipio"], "3")
    if not municipal_rows:
        raise ValueError("Nenhum resultado municipal da rede 3; confira a extração")
    directories = {
        key[0]: row for key, row in _index(
            sources["diretorio_municipio"], "id_municipio"
        ).items()
    }
    municipal_targets = _index(
        _network_rows(sources["meta_municipio"], "Municipal"), "ano", "id_municipio"
    )
    uf_results = _index(_network_rows(sources["uf"], "5"), "ano", "sigla_uf")
    uf_targets = _index(_network_rows(sources["meta_uf"], "Pública"), "ano", "sigla_uf")
    brazil_results = _index(_network_rows(sources["meta_brasil"], "Pública"), "ano")
    brazil_targets = brazil_results
    students = _student_counts(sources["alunos"])
    records: list[IndicatorRecord] = []
    issues: list[QualityIssue] = []

    for row in municipal_rows:
        year = int(row["ano"])
        if year != 2024:
            raise ValueError("O recorte suportado é 2024; não comparar outro ano à meta 2024")
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
        student_key = (str(year), municipality_id)
        if student_key not in students:
            issues.append(QualityIssue(
                "students_relationship", "error", key, "Município sem agregado de alunos"
            ))
            continue
        try:
            numeric_values = [
                row["taxa_alfabetizacao"], target["meta_alfabetizacao_2024"],
                uf_result["taxa_alfabetizacao"], uf_target["meta_alfabetizacao_2024"],
                brazil_result["taxa_alfabetizacao"], brazil_target["meta_alfabetizacao_2024"],
            ]
            if any(not 0 <= _number(value) <= 100 for value in numeric_values):
                raise ValueError("Percentual fora de 0–100")
            participation = _optional_number(target.get("percentual_participacao"))
            if participation is not None and not 0 <= participation <= 100:
                raise ValueError("Participação fora de 0–100")
        except (ValueError, TypeError, KeyError):
            issues.append(QualityIssue(
                "official_numeric_values", "error", key,
                "Indicador/meta ausente, inválido ou fora de 0–100"
            ))
            continue
        records.append(
            IndicatorRecord(
                ano=year,
                sigla_uf=uf,
                id_municipio=municipality_id,
                nome_municipio=str(directory["nome"]),
                percentual_alfabetizado=_number(row["taxa_alfabetizacao"]),
                meta_percentual=_number(target["meta_alfabetizacao_2024"]),
                total_avaliados=students[student_key],
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
        municipal_input_rows=len(municipal_rows),
    )


def _index(rows: list[dict[str, Any]], *columns: str) -> dict[tuple[str, ...], dict[str, Any]]:
    result = {}
    for row in rows:
        key = tuple(str(row[column]) for column in columns)
        if key in result:
            raise ValueError(f"Chave duplicada na fonte: {columns}={key}")
        result[key] = row
    return result


def _student_counts(rows: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    students: dict[tuple[str, str], int] = {}
    for row in rows:
        if {"id_aluno", "id_escola"} & row.keys():
            raise ValueError("Microdados: identificadores individuais não são aceitos")
        if not _is_municipal(row.get("rede")):
            continue
        key = (str(row["ano"]), str(row["id_municipio"]))
        if key in students:
            raise ValueError(f"Agregado de alunos duplicado: {key}")
        if "total_avaliados" not in row:
            raise ValueError("Use alunos_agregados.csv; microdados não são aceitos pela integração")
        count = int(str(row["total_avaliados"]))
        if count < 0:
            raise ValueError(f"Contagem negativa de alunos: {key}")
        students[key] = count
    return students


def _is_municipal(value: Any) -> bool:
    return str(value or "").strip() == "3"


def _network_rows(rows: list[dict[str, Any]], network: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("rede", "")).strip() == network]


def _number(value: Any) -> float:
    number = float(str(value).replace(",", "."))
    if not math.isfinite(number):
        raise ValueError("Valor não finito")
    return number


def _optional_number(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return _number(value)
