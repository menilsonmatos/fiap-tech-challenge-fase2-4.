"""Agregação após a Bronze, com deduplicação em disco e sem IDs na saída."""
import csv
import sqlite3
import tempfile
from collections import defaultdict
from pathlib import Path


def aggregate_students(path: Path) -> list[dict[str, str]]:
    counters = defaultdict(lambda: [0, 0, 0, 0])
    with tempfile.TemporaryDirectory(prefix="fiap-students-") as directory:
        db = sqlite3.connect(str(Path(directory) / "students.db"))
        try:
            db.execute("PRAGMA cache_size=-8192")
            db.execute("CREATE TABLE pupils (ano TEXT, municipio TEXT, escola TEXT, aluno TEXT, PRIMARY KEY(ano,municipio,escola,aluno)) WITHOUT ROWID")
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                required = {"ano", "id_municipio", "rede", "id_escola", "id_aluno", "presenca", "preenchimento_caderno", "alfabetizado"}
                if not required <= set(reader.fieldnames or []):
                    raise ValueError("Esquema de alunos brutos incompleto")
                for index, row in enumerate(reader):
                    if row["ano"] != "2024" or row["rede"] != "3":
                        raise ValueError("Alunos fora do recorte 2024/rede 3")
                    key = (row["ano"], row["id_municipio"])
                    count = counters[key]
                    count[0] += 1
                    eligible = row["presenca"] == "1" and row["preenchimento_caderno"] == "1" and row["alfabetizado"] in {"0", "1"}
                    count[1 if eligible else 2] += 1
                    if eligible:
                        if not row["id_escola"].strip() or not row["id_aluno"].strip():
                            count[3] += 1
                        else:
                            db.execute("INSERT OR IGNORE INTO pupils VALUES (?,?,?,?)", (*key, row["id_escola"], row["id_aluno"]))
                    if index % 10000 == 0:
                        db.commit()
            db.commit()
            totals = {(year, municipality): total for year, municipality, total in db.execute("SELECT ano,municipio,COUNT(*) FROM pupils GROUP BY ano,municipio")}
        finally:
            db.close()
    return [{"ano": year, "id_municipio": municipality, "rede": "3",
             "registros_origem": str(count[0]), "registros_avaliacao_valida": str(count[1]),
             "registros_avaliacao_invalida": str(count[2]), "registros_sem_identificador": str(count[3]),
             "total_avaliados": str(totals.get((year, municipality), 0))}
            for (year, municipality), count in sorted(counters.items())]
