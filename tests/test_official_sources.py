import csv
import tempfile
import unittest
from pathlib import Path

from alfabetizacao_pipeline.local_pipeline import run_official_batch
from alfabetizacao_pipeline.official_sources import integrate_official_sources, read_source_rows


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/official"


class OfficialSourcesTests(unittest.TestCase):
    def test_integrates_all_required_entities(self):
        result = integrate_official_sources(read_source_rows(FIXTURES))
        self.assertEqual(len(result.records), 2)
        self.assertEqual(result.issues, [])
        fortaleza = next(row for row in result.records if row.id_municipio == "2304400")
        self.assertEqual(fortaleza.total_avaliados, 2)
        self.assertEqual(fortaleza.taxa_alfabetizacao_uf, 60.3)
        self.assertEqual(fortaleza.meta_alfabetizacao_brasil, 60.0)

    def test_official_batch_materializes_medallion_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = run_official_batch(FIXTURES, output)
            self.assertEqual(manifest["status"], "success")
            self.assertEqual(manifest["integrated_rows"], 2)
            self.assertEqual(manifest["silver_rows"], 2)
            self.assertEqual(set(manifest["source_rows"]), {
                "municipio", "uf", "meta_brasil", "meta_uf",
                "meta_municipio", "alunos", "diretorio_municipio",
            })
            silver = output / "silver/indicadores_oficiais.csv"
            self.assertTrue(silver.exists())
            with silver.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                rows[0]["fonte"],
                "INEP / Base dos Dados - br_inep_avaliacao_alfabetizacao",
            )

    def test_reports_missing_relationship(self):
        sources = read_source_rows(FIXTURES)
        sources["meta_municipio"] = sources["meta_municipio"][:1]
        result = integrate_official_sources(sources)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.issues[0].rule, "municipal_target_relationship")


if __name__ == "__main__":
    unittest.main()
