from __future__ import annotations

from collections import defaultdict
from typing import Any

from .contracts import IndicatorRecord


def deduplicate(records: list[IndicatorRecord]) -> list[IndicatorRecord]:
    latest: dict[tuple[int, str], IndicatorRecord] = {}
    for record in records:
        current = latest.get(record.natural_key)
        if current is None or record.data_ingestao >= current.data_ingestao:
            latest[record.natural_key] = record
    return sorted(latest.values(), key=lambda r: (r.ano, r.sigla_uf, r.id_municipio))


def aggregate_by_uf(records: list[IndicatorRecord]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str], list[IndicatorRecord]] = defaultdict(list)
    for record in records:
        groups[(record.ano, record.sigla_uf)].append(record)

    result: list[dict[str, Any]] = []
    for (ano, uf), rows in sorted(groups.items()):
        total = sum(row.total_avaliados for row in rows)
        weighted = (
            sum(row.percentual_alfabetizado * row.total_avaliados for row in rows) / total
            if total
            else 0.0
        )
        target = (
            sum(row.meta_percentual * row.total_avaliados for row in rows) / total
            if total
            else 0.0
        )
        result.append(
            {
                "ano": ano,
                "sigla_uf": uf,
                "percentual_alfabetizado_ponderado": round(weighted, 2),
                "meta_percentual_ponderada": round(target, 2),
                "gap_meta_pp": round(weighted - target, 2),
                "municipios": len(rows),
                "municipios_na_meta": sum(
                    row.percentual_alfabetizado >= row.meta_percentual for row in rows
                ),
                "total_avaliados": total,
            }
        )
    return result


def vulnerability_ranking(records: list[IndicatorRecord]) -> list[dict[str, Any]]:
    rows = [
        {
            **record.to_dict(),
            "prioridade": round(record.meta_percentual - record.percentual_alfabetizado, 2),
        }
        for record in records
    ]
    rows.sort(key=lambda row: (row["ano"], -row["prioridade"], -row["total_avaliados"]))
    positions: dict[int, int] = defaultdict(int)
    for row in rows:
        positions[row["ano"]] += 1
        row["ranking_vulnerabilidade"] = positions[row["ano"]]
    return rows
