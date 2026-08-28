-- Deve retornar zero linhas. Pode ser executado por Scheduled Query/Cloud Composer.
SELECT 'duplicate_key' AS rule, CAST(ano AS STRING) AS partition_value,
       CONCAT(CAST(ano AS STRING), ':', id_municipio) AS failing_key
FROM `${PROJECT_ID}.alfabetizacao_silver.indicadores`
GROUP BY ano, id_municipio
HAVING COUNT(*) > 1
UNION ALL
SELECT 'invalid_range', CAST(ano AS STRING), CONCAT(CAST(ano AS STRING), ':', id_municipio)
FROM `${PROJECT_ID}.alfabetizacao_silver.indicadores`
WHERE percentual_alfabetizado NOT BETWEEN 0 AND 100
   OR meta_percentual NOT BETWEEN 0 AND 100
UNION ALL
SELECT 'invalid_municipality_key', CAST(ano AS STRING), CONCAT(CAST(ano AS STRING), ':', id_municipio)
FROM `${PROJECT_ID}.alfabetizacao_silver.indicadores`
WHERE NOT REGEXP_CONTAINS(id_municipio, r'^\d{7}$');

