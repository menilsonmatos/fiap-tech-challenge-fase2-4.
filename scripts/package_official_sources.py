"""Prepara ZIP para transferência manual; não acessa a rede nem inclui credenciais."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


FILES = (
    "municipio.csv", "uf.csv", "meta_alfabetizacao_brasil.csv",
    "meta_alfabetizacao_uf.csv", "meta_alfabetizacao_municipio.csv",
    "alunos_agregados.csv", "diretorio_municipio.csv",
)


def package(source, destination):
    manifest_bytes = (source / "extraction_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    entries = {entry["filename"]: entry for entry in manifest["files"].values()}
    if set(entries) != set(FILES) or len(manifest["files"]) != len(FILES):
        raise ValueError("Manifesto não corresponde aos sete extratos esperados")
    payloads = {}
    for filename in FILES:
        data = (source / filename).read_bytes()
        entry = entries[filename]
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Hash divergente: {filename}")
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
        fields = set(reader.fieldnames or [])
        if fields & {"id_aluno", "id_escola"}:
            raise ValueError(f"Identificadores individuais não permitidos: {filename}")
        if filename == "alunos_agregados.csv" and "total_avaliados" not in fields:
            raise ValueError("Arquivo de alunos não agregado")
        if sum(1 for _ in reader) != entry["rows"]:
            raise ValueError(f"Contagem divergente: {filename}")
        payloads[f"data/official/{filename}"] = data
    payloads["data/official/extraction_manifest.json"] = manifest_bytes
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusivo: nunca sobrescrever um pacote que já exista.
    with ZipFile(destination, "x", compression=ZIP_DEFLATED) as archive:
        for name, data in payloads.items():
            archive.writestr(name, data)
    with ZipFile(destination) as archive:
        if set(archive.namelist()) != set(payloads) or archive.testzip() is not None:
            raise ValueError("Falha de integridade no ZIP")
        for name, data in payloads.items():
            if archive.read(name) != data:
                raise ValueError(f"Conteúdo divergente no ZIP: {name}")
    return {"package": str(destination.resolve()), "files": len(payloads),
            "bytes": destination.stat().st_size,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("data/official"))
    parser.add_argument("--output", type=Path, default=Path("dist/dados-oficiais-2024.zip"))
    args = parser.parse_args()
    print(json.dumps(package(args.source_dir, args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
