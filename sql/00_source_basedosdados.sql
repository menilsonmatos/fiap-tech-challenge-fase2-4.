-- Integração oficial exigida pelo Tech Challenge.
-- Fonte: basedosdados.br_inep_avaliacao_alfabetizacao (INEP / Base dos Dados).
-- Esta consulta usa as seis entidades obrigatórias e o diretório de municípios
-- apenas para obter nome e sigla da UF. Execute no BigQuery com um projeto de cobrança.

WITH resultado_municipio AS (
  SELECT ano, id_municipio, taxa_alfabetizacao
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE ano = 2024 AND rede = '3'
),
meta_municipio AS (
  SELECT ano, id_municipio, meta_alfabetizacao_2024, percentual_participacao
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  WHERE ano = 2024 AND rede = 'Municipal'
),
alunos AS (
  SELECT ano, id_municipio,
    COUNT(DISTINCT TO_JSON_STRING(STRUCT(id_escola, id_aluno))) AS total_avaliados
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  WHERE ano = 2024 AND rede = '3'
    AND presenca = '1' AND preenchimento_caderno = '1'
    AND alfabetizado IN ('0', '1')
    AND NULLIF(TRIM(id_escola), '') IS NOT NULL
    AND NULLIF(TRIM(id_aluno), '') IS NOT NULL
  GROUP BY ano, id_municipio
),
resultado_uf AS (
  SELECT ano, sigla_uf, taxa_alfabetizacao
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.uf`
  WHERE ano = 2024 AND rede = '5'
),
meta_uf AS (
  SELECT ano, sigla_uf, meta_alfabetizacao_2024
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf`
  WHERE ano = 2024 AND rede = 'Pública'
),
brasil AS (
  SELECT ano, taxa_alfabetizacao, meta_alfabetizacao_2024
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil`
  WHERE ano = 2024 AND rede = 'Pública'
)
SELECT
  resultado_municipio.ano,
  diretorio.sigla_uf,
  resultado_municipio.id_municipio,
  diretorio.nome AS nome_municipio,
  resultado_municipio.taxa_alfabetizacao AS percentual_alfabetizado,
  meta_municipio.meta_alfabetizacao_2024 AS meta_percentual,
  COALESCE(alunos.total_avaliados, 0) AS total_avaliados,
  resultado_uf.taxa_alfabetizacao AS taxa_alfabetizacao_uf,
  meta_uf.meta_alfabetizacao_2024 AS meta_alfabetizacao_uf,
  brasil.taxa_alfabetizacao AS taxa_alfabetizacao_brasil,
  brasil.meta_alfabetizacao_2024 AS meta_alfabetizacao_brasil,
  meta_municipio.percentual_participacao,
  -- Diagnóstico: não eliminar registros sem correspondência por INNER JOIN.
  CASE
    WHEN diretorio.id_municipio IS NULL THEN 'sem_diretorio'
    WHEN meta_municipio.id_municipio IS NULL THEN 'sem_meta_municipal'
    WHEN resultado_uf.sigla_uf IS NULL THEN 'sem_resultado_uf_rede_5'
    WHEN meta_uf.sigla_uf IS NULL THEN 'sem_meta_uf'
    WHEN brasil.ano IS NULL THEN 'sem_meta_brasil'
    WHEN alunos.id_municipio IS NULL THEN 'sem_alunos_avaliados'
    ELSE 'relacionamentos_encontrados'
  END AS status_relacionamentos,
  'INEP / Base dos Dados - br_inep_avaliacao_alfabetizacao' AS fonte,
  CURRENT_TIMESTAMP() AS data_ingestao
FROM resultado_municipio
LEFT JOIN meta_municipio USING (ano, id_municipio)
LEFT JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS diretorio
  USING (id_municipio)
LEFT JOIN alunos USING (ano, id_municipio)
LEFT JOIN resultado_uf USING (ano, sigla_uf)
LEFT JOIN meta_uf USING (ano, sigla_uf)
LEFT JOIN brasil ON resultado_municipio.ano = brasil.ano;
