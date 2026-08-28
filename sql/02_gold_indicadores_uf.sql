CREATE OR REPLACE TABLE `${PROJECT_ID}.alfabetizacao_gold.indicadores_uf`
PARTITION BY RANGE_BUCKET(ano, GENERATE_ARRAY(2023, 2031, 1))
CLUSTER BY sigla_uf AS
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
  ano,
  sigla_uf,
  ROUND(SAFE_DIVIDE(
    SUM(percentual_alfabetizado * total_avaliados), SUM(total_avaliados)
  ), 2) AS percentual_alfabetizado_ponderado,
  ROUND(SAFE_DIVIDE(
    SUM(meta_percentual * total_avaliados), SUM(total_avaliados)
  ), 2) AS meta_percentual_ponderada,
  ROUND(SAFE_DIVIDE(
    SUM((percentual_alfabetizado - meta_percentual) * total_avaliados),
    SUM(total_avaliados)
  ), 2) AS gap_meta_pp,
  COUNT(*) AS municipios,
  COUNTIF(percentual_alfabetizado >= meta_percentual) AS municipios_na_meta,
  SUM(total_avaliados) AS total_avaliados
FROM latest
GROUP BY ano, sigla_uf;

