import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from scripts.extract_official_data import main


class ExtractionTests(unittest.TestCase):
    def run_extractor(self, output, extra_args=(), estimated_bytes=100):
        google = ModuleType("google")
        cloud = ModuleType("google.cloud")
        bigquery = ModuleType("google.cloud.bigquery")
        google.cloud = cloud
        cloud.bigquery = bigquery
        bigquery.QueryJobConfig = SimpleNamespace
        client = MagicMock()
        bigquery.Client = MagicMock(return_value=client)

        class Rows(list):
            schema = [SimpleNamespace(name="ano")]
            total_rows = 1

        def query(sql, job_config):
            return SimpleNamespace(
                total_bytes_processed=estimated_bytes,
                job_id="test-job",
                result=lambda: Rows([{"ano": 2024}]),
            )

        client.query.side_effect = query
        modules = {"google": google, "google.cloud": cloud, "google.cloud.bigquery": bigquery}
        argv = [
            "extract", "--billing-project", "test-project",
            "--output", str(output), *extra_args,
        ]
        with patch.dict("sys.modules", modules), patch("sys.argv", argv):
            with contextlib.redirect_stdout(io.StringIO()):
                main()
        return client

    def test_default_only_estimates_and_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "extract"
            client = self.run_extractor(output)
            self.assertFalse(output.exists())
            self.assertEqual(client.query.call_count, 7)
            self.assertTrue(all(
                call.kwargs["job_config"].dry_run for call in client.query.call_args_list
            ))

    def test_execute_creates_hashes_queries_and_no_legacy_student_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "extract"
            client = self.run_extractor(output, ["--execute"])
            self.assertEqual(client.query.call_count, 14)
            manifest = json.loads((output / "extraction_manifest.json").read_text())
            self.assertEqual(len(manifest["files"]), 7)
            self.assertTrue((output / "alunos_agregados.csv").exists())
            self.assertFalse((output / "alunos.csv").exists())
            for item in manifest["files"].values():
                self.assertEqual(len(item["sha256"]), 64)
                self.assertTrue(item["query"])

    def test_oversize_dry_run_aborts_before_creating_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "extract"
            with self.assertRaisesRegex(SystemExit, "limite por consulta"):
                self.run_extractor(output, ["--execute"], estimated_bytes=2**40)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
