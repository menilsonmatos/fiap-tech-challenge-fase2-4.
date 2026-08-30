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

    def test_does_not_replace_public_network_with_total_or_federal(self):
        for wrong_network in ("0", "2", "3", "6", "Pública"):
            with self.subTest(network=wrong_network):
                sources = read_source_rows(FIXTURES)
                sources["uf"][0]["rede"] = wrong_network
                result = integrate_official_sources(sources)
                self.assertEqual(result.records, [])
                self.assertEqual(len(result.issues), 2)
                self.assertTrue(all(i.rule == "official_relationships" for i in result.issues))

    def test_nonmunicipal_results_and_students_are_not_mixed(self):
        sources = read_source_rows(FIXTURES)
        sources["municipio"].append({**sources["municipio"][0], "rede": "2"})
        sources["alunos"].append({**sources["alunos"][0], "rede": "2", "total_avaliados": "999"})
        result = integrate_official_sources(sources)
        self.assertEqual(result.municipal_input_rows, 2)
        self.assertEqual(sum(r.total_avaliados for r in result.records), 3)

    def test_raw_students_are_rejected(self):
        sources = read_source_rows(FIXTURES)
        sources["alunos"] = [{"ano": "2024", "id_municipio": "2304400", "rede": "3"}]
        with self.assertRaisesRegex(ValueError, "microdados"):
            integrate_official_sources(sources)

    def test_duplicate_aggregates_are_not_summed(self):
        sources = read_source_rows(FIXTURES)
        sources["alunos"].append(sources["alunos"][0].copy())
        with self.assertRaisesRegex(ValueError, "duplicado"):
            integrate_official_sources(sources)

    def test_missing_students_are_reported(self):
        sources = read_source_rows(FIXTURES)
        sources["alunos"] = []
        result = integrate_official_sources(sources)
        self.assertEqual(result.records, [])
        self.assertTrue(all(i.rule == "students_relationship" for i in result.issues))

    def test_invalid_percentages_go_to_quarantine(self):
        for value in ("", "NaN", "inf", "101"):
            with self.subTest(value=value):
                sources = read_source_rows(FIXTURES)
                sources["municipio"][0]["taxa_alfabetizacao"] = value
                result = integrate_official_sources(sources)
                self.assertEqual(len(result.records), 1)
                self.assertEqual(result.issues[0].rule, "official_numeric_values")

    def test_empty_selection_is_not_success(self):
        sources = read_source_rows(FIXTURES)
        sources["municipio"] = []
        with self.assertRaisesRegex(ValueError, "Nenhum resultado"):
            integrate_official_sources(sources)

    def test_wrong_year_is_rejected(self):
        sources = read_source_rows(FIXTURES)
        sources["municipio"][0]["ano"] = "2023"
        with self.assertRaisesRegex(ValueError, "2024"):
            integrate_official_sources(sources)


if __name__ == "__main__":
    unittest.main()
