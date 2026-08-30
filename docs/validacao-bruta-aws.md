# Validação bruta na AWS — 30/08/2026

Execução do código `0a2aa0c`, no AWS Academy Learner Lab, região `us-east-1`.
Resultados transcritos das saídas apresentadas pelo operador e dos prints revisados;
nenhuma nova consulta à nuvem foi feita para elaborar este relatório.

## Resultados

| Medida | Resultado |
|---|---:|
| Linhas originais de alunos (2024, rede municipal) | 1.840.277 |
| Grupos municipais de alunos após agregação | 5.452 |
| Municípios de entrada | 5.448 |
| Municípios Silver / ranking | 5.232 |
| Municípios excluídos | 216 |
| UFs Gold confirmadas no Athena | 24 |
| Avaliados na Gold | 1.568.597 |
| Duração Lambda | 188.579,61 ms |
| Duração faturada registrada | 188.712 ms |
| Memória máxima / configurada | 356 / 1.024 MB |

O modo `raw_bronze_aggregate_in_silver` terminou com `success_with_quarantine`.
A auditoria local verificou sete arquivos e reconciliou as saídas: 120 ocorrências
`official_numeric_values` e 96 `municipal_target_relationship`.
As contagens coincidem com a versão anterior; isso não significa cobertura de todos
os municípios brasileiros nem comprova igualdade de cada célula entre versões.

Run ID: `20260830T195353-25baaf7309bd44ed8096fa30e8579cd6`.

## Histórico, streaming e agendamento

Dois snapshots foram preservados simultaneamente em `bronze/oficial/`, com
ingestões distintas e mesmo hash de manifesto. O S3 informou versionamento Enabled.
A segunda publicação não foi seguida de outra execução batch; não alegamos duas
execuções batch reais nem restauração de uma versão antiga do S3.

Três eventos simulados (Fortaleza, Salvador e Campinas) produziram dois envelopes
na Bronze e dois arquivos Silver, contendo os três registros processados. O rótulo
`INEP/atualização` nos eventos não os torna atualizações oficiais.
A captura da listagem de quarentena termina no comando: ela não comprova sozinha
ausência de objetos nesse prefixo.

A regra `cron(0 6 1 * ? *)` foi criada, inspecionada como DISABLED e associada à
Lambda batch com entrada `{"mode":"official"}`. Isso valida provisionamento e
configuração no Lab, mas não um disparo temporal nem a permissão efetiva de invocação
em um disparo futuro. A extração BigQuery continua manual.

## Backup e encerramento

Foram criados e depois destruídos 16 recursos; `terraform state list` terminou vazio.
O operador confirmou End Lab. Não foi verificado o saldo final da conta.

O ZIP privado `fiap-backup-bruto-B9DePx.zip`, salvo em Downloads fora do repositório,
passou no teste de integridade ZIP e teve SHA-256 igual no CloudShell e Windows:

`170114395cdcd07153fe844d337cc3c45ff8a54f0ea9a3210d64c44ebfe00077`

O backup de aproximadamente 205 MB antes de compactar contém objetos atuais do S3,
incluindo os dois snapshots e resultados. Não é exportação de todas as versões antigas.
Microdados, ZIP e arquivos de estado não devem ser publicados no Git.

O pacote de entrada tinha 105.098.932 bytes descompactados, dos quais 104.115.988
eram `alunos.csv`. O CloudShell ficou sem espaço na pasta pessoal; a extração válida
e os providers foram transferidos para `/tmp`. A extração parcial não foi utilizada.
O armazenamento temporário não substitui o backup local. O pico de disco da Lambda
não foi medido e não pode ser inferido do tamanho do CSV.

Consulte o [índice de evidências](evidencias/README.md) e o [FinOps](finops.md).
