"""Pacote privado de Bronze bruta. Nunca publicar o ZIP ou microdados no Git."""
import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from alfabetizacao_pipeline.snapshots import RAW_FILES, file_hash, validate_snapshot


def package(source, destination):
    validate_snapshot(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = (*RAW_FILES, "extraction_manifest.json")
    with ZipFile(destination, "x", compression=ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(source / name, f"data/official/{name}")
    with ZipFile(destination) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != 8:
            raise ValueError("Falha de integridade do pacote")
    return {"package": str(destination.resolve()), "files": 8,
            "bytes": destination.stat().st_size, "sha256": file_hash(destination),
            "private_raw_data": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("data/official-raw"))
    parser.add_argument("--output", type=Path, default=Path("dist/dados-oficiais-brutos-2024.zip"))
    args = parser.parse_args()
    print(json.dumps(package(args.source_dir, args.output), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
