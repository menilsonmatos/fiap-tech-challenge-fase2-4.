-- Integração oficial exigida pelo Tech Challenge.
-- Fonte: basedosdados.br_inep_avaliacao_alfabetizacao (INEP / Base dos Dados).
-- Esta consulta usa as seis entidades obrigatórias e o diretório de municípios
-- apenas para obter nome e sigla da UF. Execute no BigQuery com um projeto de cobrança.

WITH resultado_municipio AS (
  SELECT ano, id_municipio, taxa_alfabetizacao, percentual_participacao
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE ano = 2024 AND LOWER(rede) LIKE '%municip%'
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ano, id_municipio ORDER BY taxa_alfabetizacao DESC
  ) = 1
),
meta_municipio AS (
  SELECT ano, id_municipio, meta_alfabetizacao_2024
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  WHERE ano = 2024
  QUALIFY ROW_NUMBER() OVER (PARTITION BY ano, id_municipio ORDER BY rede) = 1
),
alunos AS (
  SELECT ano, id_municipio, COUNT(DISTINCT id_aluno) AS total_avaliados
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  WHERE ano = 2024 AND alfabetizado IS NOT NULL
  GROUP BY ano, id_municipio
),
resultado_uf AS (
  SELECT ano, sigla_uf, taxa_alfabetizacao
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.uf`
  WHERE ano = 2024
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ano, sigla_uf
    ORDER BY IF(LOWER(rede) LIKE '%públic%', 0, 1), rede
  ) = 1
),
meta_uf AS (
  SELECT ano, sigla_uf, meta_alfabetizacao_2024
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_uf`
  WHERE ano = 2024
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ano, sigla_uf
    ORDER BY IF(LOWER(rede) LIKE '%públic%', 0, 1), rede
  ) = 1
),
brasil AS (
  SELECT ano, taxa_alfabetizacao, meta_alfabetizacao_2024
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_brasil`
  WHERE ano = 2024
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ano ORDER BY IF(LOWER(rede) LIKE '%públic%', 0, 1), rede
  ) = 1
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
  resultado_municipio.percentual_participacao,
  'INEP / Base dos Dados - br_inep_avaliacao_alfabetizacao' AS fonte,
  CURRENT_TIMESTAMP() AS data_ingestao
FROM resultado_municipio
INNER JOIN meta_municipio USING (ano, id_municipio)
INNER JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS diretorio
  USING (id_municipio)
LEFT JOIN alunos USING (ano, id_municipio)
INNER JOIN resultado_uf USING (ano, sigla_uf)
INNER JOIN meta_uf USING (ano, sigla_uf)
CROSS JOIN brasil
WHERE resultado_municipio.taxa_alfabetizacao BETWEEN 0 AND 100
  AND meta_municipio.meta_alfabetizacao_2024 BETWEEN 0 AND 100;
