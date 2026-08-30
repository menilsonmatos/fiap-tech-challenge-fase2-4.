import unittest
from pathlib import Path

from alfabetizacao_pipeline.aws_handler import transform_csv, transform_official_csvs
from alfabetizacao_pipeline.official_sources import OFFICIAL_SOURCE_FILES


ROOT = Path(__file__).resolve().parents[1]


class AwsHandlerTests(unittest.TestCase):
    def test_batch_transform_materializes_medallion_outputs(self):
        source = (ROOT / "data/source/indicador_alfabetizacao.csv").read_bytes()
        result = transform_csv(source)
        self.assertEqual(result["manifest"]["status"], "success")
        self.assertEqual(result["manifest"]["input_rows"], 9)
        self.assertEqual(result["manifest"]["silver_rows"], 9)
        self.assertIn(b"sigla_uf", result["gold_uf"])
        self.assertIn(b"ranking_vulnerabilidade", result["gold_ranking"])

    def test_official_transform_integrates_source_tables(self):
        fixtures = ROOT / "tests/fixtures/official"
        contents = {
            name: (fixtures / filename).read_bytes()
            for name, filename in OFFICIAL_SOURCE_FILES.items()
        }
        result = transform_official_csvs(contents)
        self.assertEqual(result["manifest"]["status"], "success")
        self.assertEqual(result["manifest"]["integrated_rows"], 2)
        self.assertIn(b"taxa_alfabetizacao_brasil", result["silver"])
        contents["meta_municipio"] = contents["meta_municipio"].splitlines(keepends=True)[0]
        result = transform_official_csvs(contents)
        self.assertEqual(result["manifest"]["municipal_input_rows"], 2)
        self.assertEqual(result["manifest"]["municipal_excluded_rows"], 2)
        self.assertEqual(result["manifest"]["silver_rows"], 0)
        self.assertEqual(result["manifest"]["status"], "success_with_quarantine")
        self.assertIn(b"municipal_target_relationship", result["quality"])


if __name__ == "__main__":
    unittest.main()
