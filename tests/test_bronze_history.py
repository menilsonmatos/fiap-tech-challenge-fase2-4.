import base64
import csv
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from alfabetizacao_pipeline.aws_handler import batch_handler, streaming_handler
from alfabetizacao_pipeline.local_pipeline import run_official_batch
from alfabetizacao_pipeline.raw_students import aggregate_students
from alfabetizacao_pipeline.snapshots import RAW_FILES, file_hash, validate_snapshot
from scripts.upload_official_sources import upload_snapshot
from scripts.package_official_sources import package

FIXTURES = Path(__file__).parent / "fixtures/official"


def create_snapshot(path):
    for filename in RAW_FILES:
        if filename != "alunos.csv":
            shutil.copy2(FIXTURES / filename, path / filename)
    fields = "ano,id_municipio,rede,id_escola,id_aluno,presenca,preenchimento_caderno,alfabetizado,extra_original\n"
    rows = ["2024,2304400,3,e1,a1,1,1,1,original",
            "2024,2304400,3,e1,a1,1,1,1,duplicado",
            "2024,2304400,3,e2,a1,1,1,0,outra escola",
            "2024,2304400,3,e1,a2,0,1,1,ausente",
            "2024,2304400,3,e1,,1,1,1,sem identificador",
            "2024,2303709,3,e1,a3,1,1,1,original"]
    (path / "alunos.csv").write_text(fields + "\n".join(rows) + "\n", encoding="utf-8")
    entries = {}
    for filename in RAW_FILES:
        with (path / filename).open(encoding="utf-8", newline="") as handle:
            count = len(list(csv.DictReader(handle)))
        entries[filename] = {"filename": filename, "rows": count, "sha256": file_hash(path / filename)}
    (path / "extraction_manifest.json").write_text(json.dumps({
        "students_mode": "raw_bronze_aggregate_in_silver", "files": entries}), encoding="utf-8")


class MemoryS3:
    def __init__(self):
        self.objects = {}
        self.writes = []
        self.fail_upload = False

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body
        self.writes.append(Key)

    def upload_file(self, filename, bucket, key, **kwargs):
        if self.fail_upload:
            raise RuntimeError("Falha simulada")
        self.put_object(bucket, key, Path(filename).read_bytes())

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}

    def download_file(self, bucket, key, filename):
        Path(filename).write_bytes(self.objects[key])


class BronzeHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)
        create_snapshot(self.source)
        self.s3 = MemoryS3()

    def invoke(self, handler, event):
        with patch.dict("sys.modules", {"boto3": SimpleNamespace(client=lambda name: self.s3)}), patch.dict("os.environ", {"DATA_BUCKET": "test"}):
            return handler(event, None)

    def test_aggregate_matches_eligibility_and_composite_identity(self):
        rows = sorted(aggregate_students(self.source / "alunos.csv"), key=lambda r: r["id_municipio"], reverse=True)
        self.assertEqual([r["total_avaliados"] for r in rows], ["2", "1"])
        self.assertEqual(rows[0]["registros_origem"], "5")
        self.assertEqual(rows[0]["registros_avaliacao_invalida"], "1")
        self.assertEqual(rows[0]["registros_sem_identificador"], "1")
        self.assertNotIn("id_aluno", rows[0])

    def test_local_preserves_raw_and_repeated_ingestions(self):
        output = self.source / "output"
        first = run_official_batch(self.source, output)
        second = run_official_batch(self.source, output)
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(first["source_rows"]["alunos"], 6)
        self.assertEqual(first["silver_rows"], 2)
        self.assertEqual((Path(first["bronze_prefix"]) / "alunos.csv").read_bytes(), (self.source / "alunos.csv").read_bytes())

    def test_two_snapshots_preserve_prior_raw_files(self):
        one = upload_snapshot(self.s3, "test", self.source)
        two = upload_snapshot(self.s3, "test", self.source)
        self.assertNotEqual(one["prefix"], two["prefix"])
        self.assertEqual(len([k for k in self.s3.objects if k.endswith("/alunos.csv")]), 2)
        self.assertEqual(json.loads(self.s3.objects["control/latest_official.json"]), two)

    def test_failed_upload_keeps_previous_pointer(self):
        one = upload_snapshot(self.s3, "test", self.source)
        self.s3.fail_upload = True
        with self.assertRaises(RuntimeError):
            upload_snapshot(self.s3, "test", self.source)
        self.assertEqual(json.loads(self.s3.objects["control/latest_official.json"]), one)

    def test_modified_csv_rejected_before_upload(self):
        (self.source / "alunos.csv").write_text("alterado", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Hash"):
            upload_snapshot(self.s3, "test", self.source)
        self.assertEqual(self.s3.objects, {})

    def test_batch_reads_committed_snapshot_and_stores_history(self):
        pointer = upload_snapshot(self.s3, "test", self.source)
        first = self.invoke(batch_handler, {})
        second = self.invoke(batch_handler, {})
        self.assertNotEqual(first["run_id"], second["run_id"])
        self.assertEqual(first["source_rows"]["alunos"], 6)
        self.assertEqual(first["snapshot"], pointer)
        self.assertEqual(first["silver_rows"], 2)
        self.assertIn(f"runs/{first['run_id']}/silver/indicadores.csv", self.s3.objects)
        self.assertNotIn(b"id_aluno", self.s3.objects["silver/indicadores.csv"])

    def test_batch_rejects_tampered_s3_snapshot(self):
        pointer = upload_snapshot(self.s3, "test", self.source)
        self.s3.objects[pointer["prefix"] + "/alunos.csv"] = b"alterado"
        with self.assertRaisesRegex(ValueError, "Hash"):
            self.invoke(batch_handler, {})
        self.assertNotIn("silver/indicadores.csv", self.s3.objects)

    def test_raw_stream_is_archived_before_rejection(self):
        event = {"Records": [{"kinesis": {"data": base64.b64encode(b"not json").decode()}}]}
        result = self.invoke(streaming_handler, event)
        self.assertEqual(result, {"accepted": 0, "rejected": 1})
        self.assertTrue(self.s3.writes[0].startswith("bronze/stream/"))
        self.assertEqual(json.loads(self.s3.objects[self.s3.writes[0]]), event)
        self.invoke(streaming_handler, event)
        self.assertEqual(len([k for k in self.s3.objects if k.startswith("bronze/")]), 2)

    def test_package_includes_raw_without_extra_files(self):
        from zipfile import ZipFile
        (self.source / "secret.env").write_text("not for upload")
        destination = self.source / "package.zip"
        package(self.source, destination)
        with ZipFile(destination) as archive:
            self.assertEqual(len(archive.namelist()), 8)
            self.assertEqual(archive.read("data/official/alunos.csv"), (self.source / "alunos.csv").read_bytes())
        with self.assertRaises(FileExistsError):
            package(self.source, destination)

    def test_stream_semantic_error_is_quarantined_after_bronze(self):
        payload = json.loads((FIXTURES.parents[2] / "data/source/eventos_indicadores.jsonl").read_text(encoding="utf-8").splitlines()[0])
        payload["payload"]["percentual_alfabetizado"] = 150
        event = {"Records": [{"kinesis": {"data": base64.b64encode(json.dumps(payload).encode()).decode()}}]}
        self.assertEqual(self.invoke(streaming_handler, event), {"accepted": 0, "rejected": 1})
        self.assertFalse(any(k.startswith("silver/") for k in self.s3.objects))

    def test_stream_json_array_is_quarantined(self):
        event = {"Records": [{"kinesis": {"data": base64.b64encode(b"[]").decode()}}]}
        self.assertEqual(self.invoke(streaming_handler, event)["rejected"], 1)

    def test_monthly_schedule_is_off_by_default_and_uses_lambda_permission(self):
        root = FIXTURES.parents[2]
        variables = (root / "infra/terraform/variables.tf").read_text()
        main = (root / "infra/terraform/main.tf").read_text()
        self.assertIn('variable "enable_monthly_batch"', variables)
        self.assertRegex(variables, r'default\s*=\s*false')
        self.assertIn('cron(0 6 1 * ? *)', main)
        self.assertIn('"events.amazonaws.com"', main)
        self.assertIn('resource "aws_s3_bucket_versioning"', main)
        self.assertNotIn('resource "aws_iam_role"', main)
