import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUERY = (ROOT / "sql/00_source_basedosdados.sql").read_text(encoding="utf-8")


class OfficialSourceSqlTests(unittest.TestCase):
    def test_uses_all_required_official_tables(self):
        for table in (
            "basedosdados.br_inep_avaliacao_alfabetizacao.municipio",
            "basedosdados.br_inep_avaliacao_alfabetizacao.uf",
            "basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil",
            "basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf",
            "basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio",
            "basedosdados.br_inep_avaliacao_alfabetizacao.alunos",
            "basedosdados.br_bd_diretorios_brasil.municipio",
        ):
            self.assertIn(f"`{table}`", QUERY)

    def test_returns_canonical_contract(self):
        required_aliases = {
            "ano",
            "sigla_uf",
            "id_municipio",
            "nome_municipio",
            "percentual_alfabetizado",
            "meta_percentual",
            "total_avaliados",
            "fonte",
            "data_ingestao",
        }
        normalized = re.sub(r"\s+", " ", QUERY.lower())
        for field in required_aliases:
            self.assertRegex(normalized, rf"\b{field}\b")

    def test_filters_comparable_year_and_network(self):
        self.assertGreaterEqual(QUERY.count("ano = 2024"), 6)
        self.assertIn("rede = '3'", QUERY)
        self.assertIn("rede = '5'", QUERY)
        self.assertIn("rede = 'Municipal'", QUERY)
        self.assertIn("rede = 'Pública'", QUERY)
        self.assertNotIn("ROW_NUMBER", QUERY)

    def test_participation_comes_from_target_table(self):
        self.assertIn("meta_municipio.percentual_participacao", QUERY)
        self.assertNotIn("resultado_municipio.percentual_participacao", QUERY)


if __name__ == "__main__":
    unittest.main()
