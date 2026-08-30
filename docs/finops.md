# FinOps

O orçamento do AWS Academy Learner Lab é limitado e compartilhado ao longo do curso.

Controles adotados:

1. Região única `us-east-1`.
2. Lambda streaming com 128 MiB/30 s; batch bruto com 1.024 MiB/900 s e 4 GiB temporários.
3. Um shard Kinesis, mantido somente durante a demonstração.
4. CloudWatch Logs com retenção de sete dias.
5. S3 privado, versionado e com snapshots por ingestão para preservar o histórico exigido.
6. Athena com corte automático em 1 GiB lido por consulta.
7. Proibição arquitetural de EC2, EMR, Redshift e NAT Gateway nesta entrega.
8. `terraform destroy` obrigatório ao final da captura de evidências.
9. Regra mensal desativada por padrão; não há extração BigQuery automática na AWS.

Antes e depois de cada sessão, registre o indicador `Used $X of $50` do Learner Lab. Pare
a implantação se houver consumo inesperado e consulte o CloudWatch e os recursos ativos.

## Estimativa orçamentária — revisão de 30/08/2026

Valores em USD para cenário de referência em `us-east-1`, sem impostos, créditos do
Academy ou desconto promocional. **Não são consumo medido nem garantia de cobrança.**
O tamanho do CSV bruto e o tempo real da nova Lambda ainda precisam ser medidos.

Premissas da sessão: 4 horas de infraestrutura, um shard, uma execução batch de 120 s
com 1 GiB RAM, três invocações streaming de 1 s, 1 GB total armazenado incluindo versões,
1.000 PUT/LIST e 1.000 GET, dez consultas Athena cobradas pelo mínimo de 10 MB cada,
0,01 GB de logs. A projeção mensal usa 730 horas de Kinesis e uma execução batch.

| Item | Cálculo de referência | Sessão de 4 h | Mês de 730 h |
|---|---|---:|---:|
| Kinesis provisionado | 1 shard × horas × US$ 0,015 | 0,0600 | 10,9500 |
| Lambda compute e requests | 120 GB-s batch + 0,375 GB-s stream; US$ 0,0000166667/GB-s e US$ 0,20/milhão de requests | 0,00201 | 0,00201 |
| Disco temporário Lambda | 3,5 GiB adicionais × 120 s × US$ 0,0000000309/GB-s | 0,000013 | 0,000013 |
| S3 Standard armazenamento | 1 GB × US$ 0,023 × fração do mês | 0,00013 | 0,0230 |
| S3 requests | 1.000 PUT/LIST × 0,005/1.000 + 1.000 GET × 0,0004/1.000 | 0,0054 | 0,0054 |
| Athena | cerca de 100 MB cobrados × US$ 5/TB | 0,0005 | 0,0005 |
| CloudWatch ingestão de logs | 0,01 GB × US$ 0,50/GB | 0,0050 | 0,0050 |
| Reserva para metadados, eventos, logs armazenados e arredondamentos | Premissa orçamentária, não tarifa unitária | 0,0500 | 0,0500 |
| **Total estimado arredondado** | | **0,13** | **11,04** |

O catálogo pequeno pode ficar na franquia de objetos/acessos do Glue; a estimativa
não cria jobs Glue ou crawlers. EventBridge usa regra agendada para Lambda na mesma conta,
não Scheduler com papel IAM adicional. A reserva não é um teto técnico. Transferências
entre regiões, saída de dados, novas consultas BigQuery, retries e outras cargas da
conta não estão incluídas. Para a sessão, reservar US$ 0,50 como margem inicial e
recalcular se qualquer premissa aumentar.

Guardar um novo snapshot de 1 GB por mês aumenta o estoque em aproximadamente 1 GB
a cada ingestão; o custo de armazenamento não fica constante indefinidamente.
Manter um shard o mês inteiro domina o orçamento. Destruir o stack depois de salvar
evidências é a principal redução de custo do laboratório, não apenas clicar em End Lab.

Fontes de preços consultadas: [Kinesis](https://aws.amazon.com/es/kinesis/data-streams/pricing/),
[Lambda e disco temporário](https://aws.amazon.com/lambda/pricing/),
[S3](https://aws.amazon.com/s3/pricing/),
[exemplo AWS de tarifas S3](https://docs.aws.amazon.com/solutions/latest/live-streaming-on-aws-with-amazon-s3/cost-example-1.html),
[Athena](https://aws.amazon.com/athena/pricing/),
[CloudWatch](https://aws.amazon.com/cloudwatch/pricing/),
[Glue](https://aws.amazon.com/glue/pricing/) e [EventBridge](https://aws.amazon.com/eventbridge/pricing/).
Reconfirmar tarifas regionais no momento de implantar.

## BigQuery: custo de obtenção separado

A extração manual é cobrada no projeto GCP, não nos créditos AWS. O script apresenta
dry run e limita cada consulta a 1 GiB; sete consultas podem somar até 7 GiB se todas
forem aceitas. Calcular `bytes cobrados / 2^40 × tarifa por TiB` conforme a região e
[preços oficiais BigQuery](https://cloud.google.com/bigquery/pricing).
Como referência, US$ 6,25/TiB resulta em cerca de US$ 0,043 para 7 GiB, antes de
franquias, arredondamentos e outros serviços. Isso não estima o volume real do novo CSV.
O Sandbox pode cobrir o uso dentro de suas cotas, mas não assumir gratuidade sem verificar
o projeto e seu uso acumulado. A nova extração bruta ainda não foi executada.

## Armazenamento eficiente sem comprometer a Bronze

O recorte é limitado a 2024/rede municipal e a Gold permanece pequena. A deduplicação
em SQLite evita carregar milhões de IDs na memória. CSV mantém o esquema e os valores
do extrato, sem conversão antes da Bronze. Parquet não foi implementado: não atribuímos
à solução economias de scan que não foram medidas. Não há expiração automática dos
snapshots durante o projeto; o histórico é mantido até o encerramento explícito.
