CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.alfabetizacao_silver.indicadores` (
  ano INT64 NOT NULL,
  sigla_uf STRING NOT NULL,
  id_municipio STRING NOT NULL,
  nome_municipio STRING NOT NULL,
  percentual_alfabetizado NUMERIC NOT NULL,
  meta_percentual NUMERIC NOT NULL,
  total_avaliados INT64 NOT NULL,
  fonte STRING,
  data_ingestao TIMESTAMP,
  atingiu_meta BOOL,
  gap_meta_pp NUMERIC
)
PARTITION BY RANGE_BUCKET(ano, GENERATE_ARRAY(2023, 2031, 1))
CLUSTER BY sigla_uf, id_municipio;

CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.alfabetizacao_silver.dead_letter` (
  event_json STRING,
  issues_json STRING,
  data_ingestao TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(data_ingestao);

