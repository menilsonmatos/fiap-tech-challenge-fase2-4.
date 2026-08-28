from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .contracts import IndicatorRecord


VALID_UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
}


@dataclass(frozen=True)
class QualityIssue:
    rule: str
    severity: str
    key: str
    message: str


def validate_record(record: IndicatorRecord) -> list[QualityIssue]:
    key = f"{record.ano}:{record.id_municipio}"
    issues: list[QualityIssue] = []
    if record.ano < 2023 or record.ano > 2030:
        issues.append(QualityIssue("valid_year", "error", key, "Ano fora de 2023–2030"))
    if record.sigla_uf not in VALID_UFS:
        issues.append(QualityIssue("valid_uf", "error", key, "UF inválida"))
    if len(record.id_municipio) != 7 or not record.id_municipio.isdigit():
        issues.append(QualityIssue("municipality_key", "error", key, "Código IBGE deve ter 7 dígitos"))
    if not 0 <= record.percentual_alfabetizado <= 100:
        issues.append(QualityIssue("indicator_range", "error", key, "Indicador fora de 0–100"))
    if not 0 <= record.meta_percentual <= 100:
        issues.append(QualityIssue("target_range", "error", key, "Meta fora de 0–100"))
    if record.total_avaliados < 0:
        issues.append(QualityIssue("non_negative_students", "error", key, "Total negativo"))
    if not record.nome_municipio:
        issues.append(QualityIssue("municipality_name", "error", key, "Nome vazio"))
    if record.total_avaliados == 0:
        issues.append(QualityIssue("non_zero_students", "warning", key, "Nenhum aluno avaliado"))
    return issues


def validate_dataset(records: list[IndicatorRecord]) -> list[QualityIssue]:
    issues = [issue for record in records for issue in validate_record(record)]
    counts = Counter(record.natural_key for record in records)
    for key, count in counts.items():
        if count > 1:
            issues.append(
                QualityIssue("unique_natural_key", "error", f"{key[0]}:{key[1]}", f"{count} registros")
            )
    return issues

