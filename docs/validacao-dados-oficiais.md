# Validação dos extratos oficiais e da Gold

## Identificação e escopo

Fonte: Base dos Dados / INEP, `br_inep_avaliacao_alfabetizacao`.
Referência: 2024. Extração: 2026-08-30T16:31:30Z.
Execução local: `20260830T163220Z`.

O usuário executou as sete consultas autenticadas no BigQuery. A auditoria posterior
leu os arquivos locais, sem novas consultas nem criação de recursos AWS.
As redes e regras de elegibilidade estão descritas em [dados-oficiais.md](dados-oficiais.md).

## Volumes extraídos

| Extrato | Registros |
|---|---:|
| Município | 5.448 |
| UF | 25 |
| Meta Brasil | 1 |
| Meta UF | 27 |
| Meta município | 5.352 |
| Alunos agregados por município | 5.452 |
| Diretório de municípios | 5.448 |

O arquivo de alunos contém agregados, não identificadores individuais. As contagens
das fontes não precisam coincidir: cada entidade possui sua cobertura.

## Quarentena revisada

| Motivo observado no extrato | Municípios |
|---|---:|
| Sem registro correspondente de meta municipal | 96 |
| Registro de meta existente, mas `meta_alfabetizacao_2024` vazia | 120 |
| Total excluído | 216 |

Os 120 casos são classificados pelo pipeline na regra genérica `official_numeric_values`;
a inspeção das linhas de origem identificou o campo de meta vazio nesses casos.
Os 96 demais casos pertencem à regra `municipal_target_relationship`.
Não foram imputadas metas nem substituídas redes para preencher essas lacunas.

Reconciliação: **5.448 = 5.232 aprovados + 216 excluídos**.
Status do pipeline: `success_with_quarantine`, com 216 erros de qualidade registrados
e zero avisos. Isso não equivale a uma execução sem problemas de cobertura.

## Conferência da Silver e Gold

A auditoria local retornou `passed` e verificou:

- hashes SHA-256 e contagens dos sete CSVs contra o manifesto de extração;
- unicidade dos municípios na Silver;
- cobertura completa da entrada entre aprovados e quarentena, sem sobreposição;
- ranking com os mesmos 5.232 municípios aprovados, posições consecutivas,
  prioridade igual à meta menos o resultado e ordenação decrescente;
- 24 grupos ano/UF na Gold;
- contagens de municípios, municípios na meta e alunos por UF;
- recálculo das médias ponderadas, metas ponderadas e diferenças em pontos percentuais.

Total de avaliados na Silver/Gold: **1.568.597**.
O gap por UF é calculado antes do arredondamento; subtrair duas médias já arredondadas
pode produzir diferença de 0,01 ponto percentual em relação ao gap publicado.

As médias por UF representam somente a rede municipal com dados completos. Não são
o indicador oficial da rede pública da UF nem cobertura integral do Brasil. Os resultados
oficiais estaduais são mantidos separadamente na Silver e no ranking.
O ranking expressa déficit em relação à meta, não diagnóstico causal de vulnerabilidade.

## Reprodução da auditoria

Na raiz do projeto, após a extração e o processamento:

```powershell
python scripts/validate_official_outputs.py --source-dir data/official --output demo-output-oficial
```

O comando apenas lê os arquivos e encerra com erro se uma verificação falhar.
Foi executado com os extratos reais; os 35 testes automatizados também passaram.
Os dados e resultados permanecem locais, ignorados pelo Git. O relatório e o script
são versionados, permitindo repetir a conferência sem publicar os extratos.

## Pendências

- Executar e validar o batch oficial na AWS e consultar a nova Gold no Athena.
- Atualizar as evidências AWS e o vídeo com os dados oficiais.
- Não apresentar as capturas antigas da amostra sintética como validação dos dados reais.
