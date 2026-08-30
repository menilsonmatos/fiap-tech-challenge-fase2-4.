"""Auditoria local dos extratos e resultados; não consulta serviços de nuvem."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("data/official"))
    parser.add_argument("--output", type=Path, default=Path("demo-output-oficial"))
    args = parser.parse_args()

    def check(condition, message):
        if not condition:
            raise ValueError(message)

    extraction = json.loads((args.source_dir / "extraction_manifest.json").read_text(encoding="utf-8"))
    for info in extraction["files"].values():
        path = args.source_dir / info["filename"]
        check(hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"], f"Hash divergente: {path}")
        check(len(read_csv(path)) == info["rows"], f"Contagem divergente: {path}")

    silver = read_csv(args.output / "silver/indicadores_oficiais.csv")
    gold = read_csv(args.output / "gold/indicadores_uf.csv")
    ranking = read_csv(args.output / "gold/ranking_vulnerabilidade.csv")
    issues = [json.loads(line) for line in (args.output / "quarantine/official_quality_issues.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    key = lambda row: (row["ano"], row["id_municipio"])
    keys = {key(row) for row in silver}
    excluded = {tuple(row["key"].split(":")) for row in issues}
    source = read_csv(args.source_dir / "municipio.csv")
    check(len(keys) == len(silver), "Silver duplicada")
    check(not keys & excluded, "Município aprovado também na quarentena")
    check(keys | excluded == {key(row) for row in source}, "Cobertura de entrada divergente")
    check(len(ranking) == len(silver) and {key(row) for row in ranking} == keys, "Cobertura do ranking divergente")
    check([int(row["ranking_vulnerabilidade"]) for row in ranking] == list(range(1, len(ranking) + 1)), "Posições do ranking divergentes")
    priorities = [float(row["prioridade"]) for row in ranking]
    check(priorities == sorted(priorities, reverse=True), "Ordem do ranking divergente")
    for row in ranking:
        check(abs(float(row["prioridade"]) - round(float(row["meta_percentual"]) - float(row["percentual_alfabetizado"]), 2)) < 1e-8, "Prioridade incorreta")
    groups = defaultdict(list)
    for row in silver:
        groups[(row["ano"], row["sigla_uf"])].append(row)
    check(len(gold) == len(groups) and {(r["ano"], r["sigla_uf"]) for r in gold} == set(groups), "Cobertura UF divergente")
    for row in gold:
        members = groups[(row["ano"], row["sigla_uf"])]
        total = sum(int(r["total_avaliados"]) for r in members)
        check(total > 0, "UF sem avaliados")
        rate = sum(float(r["percentual_alfabetizado"]) * int(r["total_avaliados"]) for r in members) / total
        target = sum(float(r["meta_percentual"]) * int(r["total_avaliados"]) for r in members) / total
        expected = {"municipios": len(members), "total_avaliados": total,
                    "municipios_na_meta": sum(float(r["percentual_alfabetizado"]) >= float(r["meta_percentual"]) for r in members),
                    "percentual_alfabetizado_ponderado": round(rate, 2),
                    "meta_percentual_ponderada": round(target, 2), "gap_meta_pp": round(rate - target, 2)}
        for field, value in expected.items():
            check(abs(float(row[field]) - value) < 1e-8, f"Gold divergente: {row['sigla_uf']} / {field}")
    print(json.dumps({"status": "passed", "source_files_verified": len(extraction["files"]),
                      "silver_rows": len(silver), "ranking_rows": len(ranking), "gold_uf_rows": len(gold),
                      "total_avaliados": sum(int(r["total_avaliados"]) for r in silver),
                      "quarantine_by_rule": dict(Counter(r["rule"] for r in issues))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
