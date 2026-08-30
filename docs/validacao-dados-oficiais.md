# Validação dos extratos oficiais e da Gold

> Registro histórico da versão com alunos agregados na origem. A revisão de Bronze
> bruta, versionamento e agendamento ainda precisa de nova execução AWS. Consulte
> [aderência aos requisitos](aderencia-obrigatoria.md); não substituir estes resultados
> pelos da nova versão sem executar e conferir novamente.

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

## Validação na AWS e encerramento — 30/08/2026

O batch Lambda `20260830T174218Z` recebeu os sete extratos e retornou os mesmos
volumes locais: 5.448 entradas, 5.232 aprovados, 216 excluídos, zero avisos e
`success_with_quarantine`. A Bronze contém sete CSVs e o manifesto da extração.

Consulta executada no Athena com sucesso:

```sql
SELECT COUNT(*) AS ufs, SUM(municipios) AS municipios,
       SUM(total_avaliados) AS alunos_avaliados
FROM indicadores_uf;
```

Resultado: 24 UFs, 5.232 municípios e 1.568.597 alunos avaliados.
Essa verificação confirma totais agregados; não constitui comparação linha a linha
dos arquivos AWS com os arquivos locais.

O streaming foi testado separadamente com três eventos simulados (Campinas, Fortaleza,
Salvador), publicados no Kinesis e encontrados em dois arquivos Silver. A listagem de
quarentena ficou vazia. O texto `INEP/atualização` no campo `fonte` desses eventos é um
rótulo da fixture e não comprova procedência oficial. Eles não são atualizações reais
do INEP e não devem ser usados como evidência estatística do batch oficial.

Os resultados foram baixados para o notebook no ZIP `evidencias-aws-oficial.zip`.
A captura de encerramento mostra `0 added, 0 changed, 12 destroyed`, seguida de
`terraform state list` vazio. Isso confirma a remoção dos recursos deste estado,
não a ausência de quaisquer recursos ou custos em toda a conta do laboratório.

Consulte o [índice das capturas](evidencias/README.md). As imagens históricas da fixture
inicial não devem ser apresentadas como a validação oficial atual.

## Pendências de entrega

- Capturas de infraestrutura revisadas com e-mail/ID da conta ocultos e incluídas no índice.
- Finalizar o vídeo com dados oficiais e identificar o streaming como simulação.
- Revisar e integrar o PR antes de enviar o link final do projeto.
