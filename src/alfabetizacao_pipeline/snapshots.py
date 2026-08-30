"""Validação dos pacotes de extração antes da publicação de um snapshot."""
import csv
import hashlib
import json
from pathlib import Path

RAW_FILES = ("municipio.csv", "uf.csv", "meta_alfabetizacao_brasil.csv",
             "meta_alfabetizacao_uf.csv", "meta_alfabetizacao_municipio.csv",
             "alunos.csv", "diretorio_municipio.csv")


def file_hash(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def validate_snapshot(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "extraction_manifest.json").read_text(encoding="utf-8"))
    entries = list(manifest["files"].values())
    if len(entries) != 7 or {entry["filename"] for entry in entries} != set(RAW_FILES):
        raise ValueError("Snapshot exige sete extratos, incluindo alunos.csv bruto; não usar pacote agregado antigo")
    if manifest.get("students_mode") != "raw_bronze_aggregate_in_silver":
        raise ValueError("Manifesto não identifica a extração bruta")
    for entry in entries:
        path = directory / entry["filename"]
        if file_hash(path) != entry["sha256"]:
            raise ValueError(f"Hash divergente: {entry['filename']}")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if entry["filename"] == "alunos.csv":
                required = {"ano", "id_municipio", "rede", "id_escola", "id_aluno", "presenca", "preenchimento_caderno", "alfabetizado"}
                if not required <= set(reader.fieldnames or []):
                    raise ValueError("Esquema de alunos brutos incompleto")
            if sum(1 for _ in reader) != entry["rows"]:
                raise ValueError(f"Contagem divergente: {entry['filename']}")
    return manifest
