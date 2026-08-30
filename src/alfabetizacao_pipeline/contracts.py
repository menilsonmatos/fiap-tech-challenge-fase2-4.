from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


REQUIRED_COLUMNS = {
    "ano",
    "sigla_uf",
    "id_municipio",
    "nome_municipio",
    "percentual_alfabetizado",
    "meta_percentual",
    "total_avaliados",
}

VALID_EVENT_TYPES = {"indicador_atualizado", "meta_atualizada", "resultado_publicado"}


@dataclass(frozen=True)
class IndicatorRecord:
    ano: int
    sigla_uf: str
    id_municipio: str
    nome_municipio: str
    percentual_alfabetizado: float
    meta_percentual: float
    total_avaliados: int
    taxa_alfabetizacao_uf: float | None = None
    meta_alfabetizacao_uf: float | None = None
    taxa_alfabetizacao_brasil: float | None = None
    meta_alfabetizacao_brasil: float | None = None
    percentual_participacao: float | None = None
    fonte: str = "INEP/Base dos Dados"
    data_ingestao: str = ""

    @property
    def natural_key(self) -> tuple[int, str]:
        return self.ano, self.id_municipio

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        if not result["data_ingestao"]:
            result["data_ingestao"] = datetime.now(timezone.utc).isoformat()
        result["atingiu_meta"] = self.percentual_alfabetizado >= self.meta_percentual
        result["gap_meta_pp"] = round(
            self.percentual_alfabetizado - self.meta_percentual, 2
        )
        return result


def parse_record(raw: dict[str, Any]) -> IndicatorRecord:
    missing = REQUIRED_COLUMNS - raw.keys()
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}")
    return IndicatorRecord(
        ano=int(raw["ano"]),
        sigla_uf=str(raw["sigla_uf"]).strip().upper(),
        id_municipio=str(raw["id_municipio"]).strip(),
        nome_municipio=" ".join(str(raw["nome_municipio"]).strip().split()),
        percentual_alfabetizado=float(str(raw["percentual_alfabetizado"]).replace(",", ".")),
        meta_percentual=float(str(raw["meta_percentual"]).replace(",", ".")),
        total_avaliados=int(float(raw["total_avaliados"])),
        taxa_alfabetizacao_uf=_optional_float(raw.get("taxa_alfabetizacao_uf")),
        meta_alfabetizacao_uf=_optional_float(raw.get("meta_alfabetizacao_uf")),
        taxa_alfabetizacao_brasil=_optional_float(raw.get("taxa_alfabetizacao_brasil")),
        meta_alfabetizacao_brasil=_optional_float(raw.get("meta_alfabetizacao_brasil")),
        percentual_participacao=_optional_float(raw.get("percentual_participacao")),
        fonte=str(raw.get("fonte") or "INEP/Base dos Dados").strip(),
        data_ingestao=str(raw.get("data_ingestao") or "").strip(),
    )


def _optional_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(str(value).replace(",", "."))


def parse_event(raw: dict[str, Any]) -> IndicatorRecord:
    event_type = raw.get("event_type")
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(f"event_type inválido: {event_type!r}")
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("payload precisa ser um objeto")
    return parse_record(payload)
