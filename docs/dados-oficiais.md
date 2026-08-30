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

## Pré-requisitos

É necessário um projeto GCP habilitado para executar consultas no BigQuery. O projeto é
informado explicitamente e será o responsável por eventual processamento faturável.
Consulte a estimativa de bytes no BigQuery antes de confirmar a consulta.

```bash
python -m pip install -e ".[gcp]"
gcloud auth application-default login
```

## Extrair

```bash
python scripts/extract_official_data.py \
  --billing-project SEU_PROJETO_GCP \
  --year 2024 \
  --output data/official
```

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
- ausência de erros de relacionamento.

## Controles implementados

- cópia sem transformação de cada extrato para a Bronze;
- integridade município-diretório, município-meta e UF-meta;
- contagem distinta de alunos avaliados por município;
- validação de duplicidades, nulos, códigos IBGE, UF e intervalos percentuais;
- quarentena para relações ausentes ou valores inválidos;
- Gold com resultado versus meta e comparativos municipal, estadual e nacional.
