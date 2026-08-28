import unittest

from alfabetizacao_pipeline.contracts import parse_event, parse_record


VALID = {
    "ano": "2024",
    "sigla_uf": "ce",
    "id_municipio": "2304400",
    "nome_municipio": "  Fortaleza  ",
    "percentual_alfabetizado": "63,1",
    "meta_percentual": "64.0",
    "total_avaliados": "13120",
}


class ContractTests(unittest.TestCase):
    def test_parses_and_normalizes_record(self):
        record = parse_record(VALID)
        self.assertEqual(record.sigla_uf, "CE")
        self.assertEqual(record.nome_municipio, "Fortaleza")
        self.assertEqual(record.percentual_alfabetizado, 63.1)

    def test_rejects_missing_columns(self):
        with self.assertRaisesRegex(ValueError, "Colunas obrigatórias"):
            parse_record({"ano": 2024})

    def test_rejects_unknown_event(self):
        with self.assertRaisesRegex(ValueError, "event_type"):
            parse_event({"event_type": "apagamento", "payload": VALID})


if __name__ == "__main__":
    unittest.main()

