import unittest

from alfabetizacao_pipeline.official_queries import extraction_queries


class OfficialQueriesTests(unittest.TestCase):
    def test_exact_networks(self):
        queries = extraction_queries()
        self.assertEqual(len(queries), 7)
        self.assertIn("rede = '3'", queries["municipio"])
        self.assertIn("rede = '5'", queries["uf"])
        self.assertIn("rede = 'Municipal'", queries["meta_alfabetizacao_municipio"])
        for table in ("meta_alfabetizacao_uf", "meta_alfabetizacao_brasil"):
            self.assertIn("rede = 'Pública'", queries[table])

    def test_student_eligibility_and_composite_identity(self):
        query = extraction_queries()["alunos_agregados"]
        self.assertTrue(query.startswith("WITH"))
        for predicate in (
            "rede = '3'", "presenca = '1'", "preenchimento_caderno = '1'",
            "alfabetizado IN ('0', '1')", "STRUCT(id_escola, id_aluno)",
            "COUNT(DISTINCT IF", "registros_sem_identificador",
        ):
            self.assertIn(predicate, query)

    def test_aggregated_output_does_not_group_by_student(self):
        query = extraction_queries()["alunos_agregados"]
        self.assertTrue(query.strip().endswith("GROUP BY ano, id_municipio, rede"))
        self.assertNotIn("alunos", extraction_queries())
        self.assertIn("AS total_avaliados", query)

    def test_year_is_not_silently_compared_with_2024_target(self):
        with self.assertRaises(ValueError):
            extraction_queries(2023)


if __name__ == "__main__":
    unittest.main()
