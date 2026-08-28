# Runbook operacional

## Batch falhou

1. Verificar logs do job e `run_id`.
2. Confirmar disponibilidade e esquema da fonte.
3. Inspecionar quarentena; não apagar o Bronze.
4. Corrigir adaptador/contrato e reexecutar com novo `run_id`.
5. Validar contagens Bronze→Silver→Gold e registrar incidente.

## Dead letter maior que zero

1. Consultar `alfabetizacao_silver.dead_letter`.
2. Agrupar por regra violada e `event_type`.
3. Se for evento malformado, corrigir produtor; se for evolução de contrato, versionar.
4. Reprocessar somente depois de a causa estar corrigida.

## Gold desatualizada

1. Verificar máximo `data_ingestao` na Silver.
2. Confirmar que assertions retornam zero linhas.
3. Executar SQL Gold idempotente.
4. Comparar contagem e indicador ponderado com a execução anterior.

## Custo anômalo

1. Filtrar billing por labels `project` e `environment`.
2. Encerrar job streaming ocioso.
3. Consultar bytes processados e confirmar filtro de partição.
4. Revisar autoscaling, staging e lifecycle.

## Rollback

A Bronze é imutável. Para rollback, reconstruir Silver/Gold a partir do `run_id` anterior
em tabelas temporárias, executar qualidade e trocar as views de consumo de forma atômica.

