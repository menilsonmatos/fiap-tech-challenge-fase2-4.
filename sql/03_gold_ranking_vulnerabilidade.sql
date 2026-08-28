CREATE OR REPLACE TABLE `${PROJECT_ID}.alfabetizacao_gold.ranking_vulnerabilidade`
PARTITION BY RANGE_BUCKET(ano, GENERATE_ARRAY(2023, 2031, 1))
CLUSTER BY sigla_uf, id_municipio AS
WITH latest AS (
  SELECT * EXCEPT(row_number)
  FROM (
    SELECT *, ROW_NUMBER() OVER (
      PARTITION BY ano, id_municipio ORDER BY data_ingestao DESC
    ) AS row_number
    FROM `${PROJECT_ID}.alfabetizacao_silver.indicadores`
  )
  WHERE row_number = 1
)
SELECT
  *,
  ROUND(meta_percentual - percentual_alfabetizado, 2) AS prioridade,
  DENSE_RANK() OVER (
    PARTITION BY ano ORDER BY meta_percentual - percentual_alfabetizado DESC, total_avaliados DESC
  ) AS ranking_vulnerabilidade
FROM latest;

