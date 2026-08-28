import unittest

from alfabetizacao_pipeline.contracts import IndicatorRecord
from alfabetizacao_pipeline.transforms import aggregate_by_uf, deduplicate, vulnerability_ranking


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            IndicatorRecord(2024, "CE", "2304400", "Fortaleza", 60, 65, 100),
            IndicatorRecord(2024, "CE", "2303709", "Caucaia", 50, 65, 50),
        ]

    def test_weighted_average(self):
        row = aggregate_by_uf(self.records)[0]
        self.assertEqual(row["percentual_alfabetizado_ponderado"], 56.67)
        self.assertEqual(row["total_avaliados"], 150)

    def test_vulnerability_ranking(self):
        rows = vulnerability_ranking(self.records)
        self.assertEqual(rows[0]["nome_municipio"], "Caucaia")
        self.assertEqual(rows[0]["ranking_vulnerabilidade"], 1)

    def test_latest_record_wins(self):
        older = IndicatorRecord(2024, "CE", "2304400", "Fortaleza", 60, 65, 100, data_ingestao="2024-01-01")
        newer = IndicatorRecord(2024, "CE", "2304400", "Fortaleza", 61, 65, 100, data_ingestao="2024-02-01")
        self.assertEqual(deduplicate([older, newer])[0].percentual_alfabetizado, 61)


if __name__ == "__main__":
    unittest.main()

