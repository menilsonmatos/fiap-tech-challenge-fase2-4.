# Extração e integração dos dados oficiais

## Fonte

O projeto utiliza `basedosdados.br_inep_avaliacao_alfabetizacao`, publicado pelo INEP na
Base dos Dados. A integração cobre as entidades exigidas pelo Tech Challenge:

| Entidade | Tabela BigQuery | Chave usada |
|---|---|---|
| UF | `uf` | `ano`, `sigla_uf` |
| Meta Brasil | `meta_alfabetizacao_brasil` | `ano` |
| Meta por UF | `meta_alfabetizacao_uf` | `ano`, `sigla_uf` |
| Meta por município | `meta_alfabetizacao_municipio` | `ano`, `id_municipio` |
| Município | `municipio` | `ano`, `id_municipio` |
| Alunos | `alunos` | `ano`, `id_municipio`, `id_escola`, `id_aluno` |

O diretório `br_bd_diretorios_brasil.municipio` complementa nome do município e UF.

## Recorte e redes confirmados no BigQuery

O recorte suportado é **2024**, comparado à coluna `meta_alfabetizacao_2024`.
Não há seleção automática de outra rede quando falta um resultado.

| Fonte | Filtro exato |
|---|---|
| `municipio` e `alunos` | `rede = '3'` (Municipal) |
| `uf` | `rede = '5'` (Pública: Estadual e Municipal) |
| `meta_alfabetizacao_municipio` | `rede = 'Municipal'` |
| `meta_alfabetizacao_uf` e `meta_alfabetizacao_brasil` | `rede = 'Pública'` |

A rede `5` não inclui a federal; a rede `6` inclui. Não são intercambiáveis.
Os filtros foram confirmados no dicionário oficial retornado pelo BigQuery.
`percentual_participacao` vem da tabela de metas municipais, não de `municipio`.

### Alunos: agregação antes da transferência

`alunos_agregados.csv` substitui o antigo `alunos.csv`. A consulta seleciona rede `3`,
presença `1`, prova preenchida `1` e `alfabetizado IN ('0', '1')`. Conta pares distintos
`(id_escola, id_aluno)` com identificadores não vazios por ano e município; alunos não
alfabetizados também são contados entre os avaliados. Os identificadores são usados
somente dentro do BigQuery e não são exportados.

O agregado inclui contagens de registros originais, avaliações válidas/inválidas e
identificadores ausentes. Não é uma cópia de microdados brutos: é uma redução na origem
por privacidade e uso de memória. A Bronze preserva esse extrato agregado como recebido;
os outros extratos preservam suas colunas originais, com filtro de ano/rede.

Preservar o conteúdo do extrato não significa armazenamento imutável. Localmente são
criadas cópias por ingestão; na AWS, o upload usa chaves fixas em `bronze/oficial/` e pode
substituir arquivos anteriores. Não há versionamento habilitado no bucket. Conserve os
pacotes de extração e consulte o [runbook](runbook.md) antes de substituir dados.

O total de avaliados é uma contagem, não a soma dos pesos amostrais. A média municipal
ponderada produzida na Gold é um indicador analítico do recorte, não uma reprodução do
ICA oficial da UF. O resultado publicado da UF é mantido em campo separado na Silver
e no ranking, sem ser substituído pela média calculada.

## Pré-requisitos

É necessário um projeto GCP habilitado para executar consultas no BigQuery. O projeto é
informado explicitamente e será o responsável por eventual processamento faturável.
Consulte a estimativa de bytes no BigQuery antes de confirmar a consulta.

```bash
python -m pip install -e ".[gcp]"
gcloud auth application-default login
```

## Estimar antes de extrair

```bash
python scripts/extract_official_data.py \
  --billing-project SEU_PROJETO_GCP \
  --year 2024 \
  --output data/official
```

Sem `--execute`, o script apenas valida/estima as sete consultas (dry run). Confira os
bytes exibidos. Cada consulta tem limite padrão de 1 GiB; o script não aumenta o limite
sozinho. Para extrair após a revisão, repita o comando acrescentando `--execute`:

```bash
python scripts/extract_official_data.py \
  --billing-project SEU_PROJETO_GCP \
  --year 2024 \
  --output data/official \
  --execute
```

O destino precisa estar vazio, evitando misturar versões ou reutilizar arquivos de uma
tentativa incompleta. `extraction_manifest.json` registra consultas, contagens, hashes
SHA-256, data e IDs dos jobs. Esse manifesto é criado somente ao concluir as sete extrações.

O diretório `data/official` é ignorado pelo Git. Não publique microdados ou identificadores
de alunos no repositório. A Silver contém somente agregações municipais.

## Processar localmente

```bash
python -m alfabetizacao_pipeline.cli batch-official \
  --source-dir data/official \
  --output demo-output
```

Verifique no manifesto:

- `source` apontando para INEP / Base dos Dados;
- todas as entidades em `source_rows`;
- `integrated_rows` e `silver_rows` maiores que zero;
- `municipal_input_rows = silver_rows + municipal_excluded_rows`;
- revisão das ocorrências em `quarantine/official_quality_issues.jsonl`.

Ausência de meta, UF ou agregado de alunos gera ocorrência identificada por ano/município
e exclui o registro da Gold. Um indicador nulo ou inválido também vai à quarentena. Uma
seleção municipal vazia ou agregados duplicados interrompem o processamento, sem sucesso
falso. O status pode ser `success_with_quarantine` quando a cobertura oficial difere.
As contagens 5.448 resultados e 5.352 metas de 2024 não provam, sozinhas, quais IDs faltam:
é a junção e seu relatório de qualidade que identificam as diferenças.

## Controles implementados

- cópia sem nova transformação dos extratos (incluindo alunos já agregados) para a Bronze;
- integridade município-diretório, município-meta e UF-meta;
- contagem distinta de pares escola/aluno elegíveis na origem, agregada por município;
- validação de duplicidades, nulos, códigos IBGE, UF e intervalos percentuais;
- quarentena para relações ausentes ou valores inválidos;
- Gold com resultado versus meta e comparativos municipal, estadual e nacional.
