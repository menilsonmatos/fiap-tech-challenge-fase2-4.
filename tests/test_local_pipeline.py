import tempfile
import unittest
from pathlib import Path

from alfabetizacao_pipeline.local_pipeline import run_batch, simulate_stream


ROOT = Path(__file__).resolve().parents[1]


class LocalPipelineTests(unittest.TestCase):
    def test_batch_creates_all_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = run_batch(ROOT / "data/source/indicador_alfabetizacao.csv", output)
            self.assertEqual(manifest["status"], "success")
            self.assertTrue((output / "silver/indicadores.csv").exists())
            self.assertTrue((output / "gold/indicadores_uf.csv").exists())
            self.assertTrue((output / "gold/ranking_vulnerabilidade.csv").exists())

    def test_stream_simulation(self):
        with tempfile.TemporaryDirectory() as directory:
            result = simulate_stream(ROOT / "data/source/eventos_indicadores.jsonl", Path(directory))
            self.assertEqual(result, {"accepted": 3, "rejected": 0})


if __name__ == "__main__":
    unittest.main()

