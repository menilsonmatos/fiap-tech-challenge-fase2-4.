import unittest
from pathlib import Path

from alfabetizacao_pipeline.aws_handler import transform_csv


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


if __name__ == "__main__":
    unittest.main()
