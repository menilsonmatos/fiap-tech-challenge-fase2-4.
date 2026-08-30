# Pipeline Híbrido para Análise da Alfabetização no Brasil

Tech Challenge — Fase 2, FIAP Pós-Tech AI Scientist.

O projeto implementa uma pipeline batch e streaming em Arquitetura Medalhão para analisar
indicadores municipais de alfabetização. A execução local é reproduzível e a implementação
cloud usa o AWS Academy Learner Lab na região `us-east-1`.

## Objetivo

O Indicador Criança Alfabetizada mede a proporção de estudantes que atingem o nível
de alfabetização esperado ao final do 2º ano do ensino fundamental. No contexto do
Compromisso Nacional Criança Alfabetizada, integrar resultados e metas permite identificar
diferenças territoriais e apoiar prioridades de acompanhamento educacional. O projeto
organiza essas informações para gestores públicos; não explica causalmente o desempenho
nem substitui avaliações pedagógicas. Usa o recorte municipal de 2024, com referências
publicadas para UF e Brasil.

A camada Gold responde quais UFs e municípios estão abaixo da meta, calcula o indicador
ponderado pelos alunos avaliados e prioriza municípios pelo déficit educacional. O ranking
apoia análise e não representa diagnóstico causal ou decisão automatizada.

## Arquitetura

```mermaid
flowchart LR
  BD[INEP / Base dos Dados - BigQuery] --> EX[Extracao bruta e upload]
  EX --> B[S3 Bronze - snapshots privados]
  M[EventBridge mensal - desativado por padrao] --> LB[Lambda batch]
  B --> LB --> S[Silver batch - agregacao e integracao]
  LB --> G[S3 Gold]
  EV[Eventos simulados] --> K[Kinesis] --> LS[Lambda streaming]
  LS --> BS[Bronze streaming - envelope original]
  BS --> SS[Silver streaming e quarentena]
  G --> GC[Glue Data Catalog - indicadores_uf] --> A[Athena]
  LB -. logs .-> CW[CloudWatch]
  LS -. logs .-> CW
```

| Camada | Conteúdo |
|---|---|
| Bronze | Extratos brutos por ingestão e envelopes originais de streaming; bucket versionado |
| Silver | registros tipados, validados, deduplicados e em quarentena quando inválidos |
| Gold | indicadores ponderados por UF e ranking municipal de vulnerabilidade |

Alunos chegam sem agregação do BigQuery; a contagem elegível/deduplicada é calculada
depois da Bronze, com SQLite temporário em disco. Somente agregados chegam à Silver/Gold.
Cada upload cria um snapshot próprio e publica seu ponteiro apenas após concluir todos
os arquivos. Os resultados batch também são preservados por execução. Os caminhos
Silver/Gold consultados atualmente pelo Athena são projeções substituíveis.
O versionamento protege substituições, mas não é Object Lock nem proteção contra um
administrador ou `terraform destroy`. Consulte o [runbook](docs/runbook.md).

**Status desta revisão:** os novos caminhos de Bronze bruta, histórico e agendamento
exigem nova extração e demonstração AWS. As evidências de 30/08 abaixo comprovam a
versão anterior, com alunos agregados na origem.

## Estrutura

```text
data/source/                 fixtures sintéticas exclusivas para testes e streaming
data/official/               extratos oficiais locais (ignorado pelo Git)
docs/                        decisões, FinOps, operação e implantação
infra/terraform/             infraestrutura AWS como código
scripts/publish_events.py    publicação de eventos no Kinesis
sql/                         fonte oficial e consultas analíticas
src/alfabetizacao_pipeline/  pipeline local e handlers AWS Lambda
tests/                       testes unitários e de integração
demo-local.ps1               demonstração offline em um comando
```

## Pipeline oficial

A extração real e a validação local foram concluídas em 30/08/2026: 5.232 municípios
aprovados, 216 em quarentena por ausência de meta e 24 UFs na Gold.
Veja [o relatório de validação oficial](docs/validacao-dados-oficiais.md).
A demonstração AWS com esses extratos foi concluída: o batch reproduziu as contagens
locais e o Athena confirmou os totais. Os 12 recursos do projeto foram removidos ao final.

A entrada principal é o conjunto `br_inep_avaliacao_alfabetizacao`, publicado pelo INEP
na Base dos Dados. O pipeline integra `municipio`, `uf`, `meta_alfabetizacao_brasil`,
`meta_alfabetizacao_uf`, `meta_alfabetizacao_municipio` e `alunos`; o diretório de
municípios fornece nome e sigla da UF.

Após extrair as fontes conforme [docs/dados-oficiais.md](docs/dados-oficiais.md), execute:

```powershell
$env:PYTHONPATH = "src"
python -m alfabetizacao_pipeline.cli batch-official `
  --source-dir data/official-raw `
  --output work-validation-raw
```

Os extratos oficiais não são publicados no Git. A extração padrão preserva `alunos.csv`
bruto (recorte 2024/rede municipal), inclusive colunas originais. Mantenha os microdados
somente no notebook e na Bronze privada; não envie o ZIP a um repositório público.
O modo agregado antigo continua legível localmente para comparação histórica, mas é
recusado no novo upload AWS. O manifesto registra a
origem, os volumes e a quantidade de municípios excluídos por inconsistências.
Consulte o guia para estimar as consultas antes de usar `--execute`.

## Demonstração técnica local

Requer Python 3.11 ou superior e não precisa de internet:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\demo-local.ps1
```

Sem os extratos oficiais, o script usa fixtures sintéticas apenas para testar código e
streaming. Seus resultados não são evidência estatística. Veja [DEMO_LOCAL.md](DEMO_LOCAL.md).

## Implementação AWS

A versão cloud usa somente serviços gerenciados de baixo custo:

- S3 para Bronze, Silver, Gold, quarentena e resultados do Athena;
- Lambda para batch e streaming;
- Kinesis Data Streams para eventos;
- Glue Data Catalog e Athena para descoberta e consulta;
- CloudWatch para logs e métricas;
- Terraform para provisionamento e destruição reproduzíveis.

O passo a passo está em [docs/implantacao-aws.md](docs/implantacao-aws.md). A implantação
deve ocorrer no Learner Lab, em `us-east-1`, e ser destruída após a gravação das evidências.

## Fonte dos dados

A fonte obrigatória é a [Avaliação da Alfabetização do INEP na Base dos Dados](https://basedosdados.org/dataset/073a39d4-89cf-4068-b1e8-34ed0d9c0b72).
A extração reproduzível está em `scripts/extract_official_data.py`, e a consulta integrada
de referência está em `sql/00_source_basedosdados.sql`. O adaptador devolve o contrato:

`ano`, `sigla_uf`, `id_municipio`, `nome_municipio`, `percentual_alfabetizado`,
`meta_percentual`, `total_avaliados`, comparativos de UF/Brasil, `fonte` e `data_ingestao`.

## Qualidade e segurança

- chave natural `(ano, id_municipio)`; duplicidades no conjunto são erros de qualidade;
- percentuais entre 0 e 100, UF válida e código IBGE com sete dígitos;
- registros inválidos enviados à quarentena sem descarte silencioso;
- S3 privado, criptografia AES-256 e bloqueio de acesso público;
- funções Lambda executadas com a `LabRole` fornecida pelo AWS Academy Learner Lab;
- em produção, recomenda-se uma função IAM exclusiva com privilégio mínimo;
- nenhuma credencial ou dado individual de aluno no repositório.

## FinOps

O desenho evita clusters e recursos ociosos. Lambda cobra por invocação/duração; o Kinesis
usa apenas um shard durante a demonstração; logs ficam sete dias; e o Athena limita cada
consulta a 1 GiB lido. Consulte [docs/finops.md](docs/finops.md).

O batch mensal usa uma regra EventBridge no dia 1 às 06:00 UTC, desativada por padrão.
Ela processa o último snapshot completo já transferido; a extração autenticada do
BigQuery continua sendo uma etapa manual. Não há credencial GCP dentro da Lambda.

## Escolhas e trade-offs

- **Batch vs streaming:** batch integra o recorte histórico completo; streaming demonstra
  chegada quase imediata de eventos simulados e fica separado da Gold oficial.
- **Lake vs warehouse:** S3 guarda arquivos e histórico; Glue cataloga a Gold e Athena
  permite SQL sem manter um warehouse dedicado. Não há transações entre todos os objetos.
- **Custo vs desempenho:** Lambda elimina servidores permanentes, mas impõe limite de
  tempo e disco. SQLite permite deduplicar alunos sem manter todos os IDs na RAM.
  O batch usa 1 GiB RAM, até 900 s e 4 GiB temporários; o recorte bruto real ainda
  precisa ser medido. Volumes maiores exigiriam outra estratégia, fora desta entrega.
- **Formato:** CSV conserva o extrato e dispensa dependências na Lambda. Snapshots e
  prefixos organizam a ingestão; a tabela analítica atual é pequena e não particionada.
  Parquet é uma otimização futura, não implementada nem contabilizada como benefício.

## Uso futuro em IA

A Gold pode alimentar regressão de indicadores e clustering territorial após enriquecimento
com Censo Escolar e variáveis socioeconômicas. O split deve ser temporal/geográfico e os
resultados precisam de auditoria de viés por UF e porte municipal.

## Evidências da validação na AWS

A infraestrutura foi implantada e validada no AWS Academy Learner Lab, em `us-east-1`.
Em 30/08/2026, a execução oficial `20260830T174218Z` aprovou 5.232 municípios e
separou 216 em quarentena. O Athena confirmou 24 UFs e 1.568.597 alunos avaliados.
O streaming foi validado separadamente com três eventos simulados, não dados oficiais.
Veja o [índice das evidências atuais](docs/evidencias/README.md).

As capturas abaixo são históricas, da fixture inicial; não substituem as evidências
atuais dos dados oficiais.

| Etapa | Evidência |
|---|---|
| Implantação das funções e integração | [Terraform aplicado](docs/evidencias/terraform_implantado.png) |
| Processamento de 9 registros sem erros | [Execução batch](docs/evidencias/processamento_batch.png) |
| Objetos nas camadas Bronze, Silver e Gold | [Camadas no S3](docs/evidencias/camadas_s3.png) |
| Publicação dos eventos simulados | [Streaming](docs/evidencias/streaming.png) |
| Stream provisionado e ativo | [Kinesis Data Streams](docs/evidencias/data-stream-kinesis.png) |
| Funções batch e streaming em Python 3.12 | [AWS Lambda](docs/evidencias/lambda.png) |
| Consulta analítica concluída com sucesso | [Amazon Athena](docs/evidencias/athena.png) |
| Encerramento sem recursos remanescentes | [Terraform destroy](docs/evidencias/terraform_destroy.png) |

## Limitações

- as fixtures em `data/source` e `tests/fixtures` existem somente para testes automatizados;
- a execução final exige extratos reais da Base dos Dados em `data/official`;
- o Learner Lab restringe regiões, serviços, sessão e orçamento;
- a infraestrutura AWS precisa ser destruída ao final da demonstração;
- o projeto entrega a base analítica, não um modelo de IA treinado.
