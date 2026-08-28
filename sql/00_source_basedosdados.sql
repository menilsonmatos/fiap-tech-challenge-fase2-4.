-- Fonte oficial: Avaliação da Alfabetização (INEP), publicada pela Base dos Dados.
-- A consulta é executada no projeto GCP do usuário (que arca com o processamento)
-- e devolve exatamente o contrato canônico esperado pelo pipeline.
--
-- Recorte: resultado municipal da rede municipal em 2024. Esse é o primeiro ano
-- para o qual a tabela oficial publica uma meta anual diretamente comparável.

WITH resultado AS (
  SELECT
    ano,
    id_municipio,
    taxa_alfabetizacao
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.municipio`
  WHERE ano = 2024
    AND LOWER(rede) = 'municipal'
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ano, id_municipio
    ORDER BY taxa_alfabetizacao DESC
  ) = 1
),
meta AS (
  SELECT
    ano,
    id_municipio,
    meta_alfabetizacao_2024 AS meta_percentual
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.meta_alfabetizacao_municipio`
  WHERE ano = 2024
    AND LOWER(rede) = 'municipal'
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ano, id_municipio
    ORDER BY meta_alfabetizacao_2024 DESC
  ) = 1
),
avaliados AS (
  SELECT
    ano,
    id_municipio,
    COUNT(DISTINCT id_aluno) AS total_avaliados
  FROM `basedosdados.br_inep_avaliacao_alfabetizacao.alunos`
  WHERE ano = 2024
    AND LOWER(rede) = 'municipal'
    AND alfabetizado IS NOT NULL
  GROUP BY ano, id_municipio
)
SELECT
  resultado.ano,
  diretorio.sigla_uf,
  resultado.id_municipio,
  diretorio.nome AS nome_municipio,
  resultado.taxa_alfabetizacao AS percentual_alfabetizado,
  meta.meta_percentual,
  COALESCE(avaliados.total_avaliados, 0) AS total_avaliados,
  'Base dos Dados / INEP - Avaliacao da Alfabetizacao' AS fonte,
  CURRENT_TIMESTAMP() AS data_ingestao
FROM resultado
INNER JOIN meta USING (ano, id_municipio)
LEFT JOIN avaliados USING (ano, id_municipio)
INNER JOIN `basedosdados.br_bd_diretorios_brasil.municipio` AS diretorio
  USING (id_municipio)
WHERE resultado.taxa_alfabetizacao BETWEEN 0 AND 100
  AND meta.meta_percentual BETWEEN 0 AND 100
  AND diretorio.sigla_uf IS NOT NULL
  AND diretorio.nome IS NOT NULL;
