import unittest

from alfabetizacao_pipeline.contracts import IndicatorRecord
from alfabetizacao_pipeline.quality import validate_dataset, validate_record


class QualityTests(unittest.TestCase):
    def test_valid_record_has_no_issues(self):
        record = IndicatorRecord(2024, "CE", "2304400", "Fortaleza", 63.1, 64.0, 100)
        self.assertEqual(validate_record(record), [])

    def test_detects_invalid_values(self):
        record = IndicatorRecord(2022, "XX", "123", "", 101, -1, -5)
        rules = {issue.rule for issue in validate_record(record)}
        self.assertTrue({"valid_year", "valid_uf", "municipality_key", "indicator_range", "target_range"} <= rules)

    def test_detects_duplicate_natural_key(self):
        record = IndicatorRecord(2024, "CE", "2304400", "Fortaleza", 63.1, 64.0, 100)
        issues = validate_dataset([record, record])
        self.assertIn("unique_natural_key", {issue.rule for issue in issues})


if __name__ == "__main__":
    unittest.main()

