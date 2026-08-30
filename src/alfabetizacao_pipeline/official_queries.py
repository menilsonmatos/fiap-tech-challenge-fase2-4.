"""Consultas de extração alinhadas ao dicionário da Base dos Dados.

Não executa consultas ao importar. Os alunos são agregados na origem: nenhum
identificador individual é exportado ao notebook, S3 ou Lambda.
"""

DATASET = "basedosdados.br_inep_avaliacao_alfabetizacao"


def extraction_queries(year: int = 2024) -> dict[str, str]:
    if year != 2024:
        raise ValueError("O recorte validado deste pipeline é 2024")
    filters = {
        "municipio": "rede = '3'",
        "uf": "rede = '5'",
        "meta_alfabetizacao_brasil": "rede = 'Pública'",
        "meta_alfabetizacao_uf": "rede = 'Pública'",
        "meta_alfabetizacao_municipio": "rede = 'Municipal'",
    }
    queries = {
        table: f"SELECT * FROM `{DATASET}.{table}` WHERE ano = {year} AND {condition}"
        for table, condition in filters.items()
    }
    queries["alunos_agregados"] = f"""WITH selecionados AS (
  SELECT ano, id_municipio, rede, id_escola, id_aluno,
    COALESCE(presenca = '1' AND preenchimento_caderno = '1'
      AND alfabetizado IN ('0', '1'), FALSE) AS avaliacao_valida
  FROM `{DATASET}.alunos`
  WHERE ano = {year} AND rede = '3'
)
SELECT ano, id_municipio, rede,
  COUNT(*) AS registros_origem,
  COUNTIF(avaliacao_valida) AS registros_avaliacao_valida,
  COUNTIF(NOT avaliacao_valida) AS registros_avaliacao_invalida,
  COUNTIF(avaliacao_valida AND
    (NULLIF(TRIM(id_escola), '') IS NULL OR NULLIF(TRIM(id_aluno), '') IS NULL))
    AS registros_sem_identificador,
  COUNT(DISTINCT IF(avaliacao_valida
    AND NULLIF(TRIM(id_escola), '') IS NOT NULL
    AND NULLIF(TRIM(id_aluno), '') IS NOT NULL,
    TO_JSON_STRING(STRUCT(id_escola, id_aluno)), NULL)) AS total_avaliados
FROM selecionados
GROUP BY ano, id_municipio, rede
"""
    queries["diretorio_municipio"] = f"""
SELECT DISTINCT d.id_municipio, d.nome, d.sigla_uf
FROM `basedosdados.br_bd_diretorios_brasil.municipio` AS d
INNER JOIN `{DATASET}.municipio` AS m USING (id_municipio)
WHERE m.ano = {year} AND m.rede = '3'
"""
    return queries
