# Dados oficiais: Bronze bruta e integração Silver

## Fonte e recorte

Fonte: `basedosdados.br_inep_avaliacao_alfabetizacao`, INEP / Base dos Dados.
O recorte suportado é 2024, comparado à coluna `meta_alfabetizacao_2024`.

| Entidade | Filtro |
|---|---|
| `municipio`, `alunos` | `rede = '3'` (Municipal) |
| `uf` | `rede = '5'` (Estadual e Municipal, sem Federal) |
| `meta_alfabetizacao_municipio` | `rede = 'Municipal'` |
| `meta_alfabetizacao_uf`, `meta_alfabetizacao_brasil` | `rede = 'Pública'` |

O diretório `br_bd_diretorios_brasil.municipio` fornece nome e UF. Não há troca automática
de rede para preencher lacunas. Participação vem da tabela de metas municipais.

## Extração bruta e privacidade

As seis entidades são exportadas com `SELECT *`, apenas com filtros de ano/rede.
`alunos.csv` preserva as linhas e colunas originais do recorte, inclusive alunos ausentes
e identificadores de escola/aluno. Não há agregação, deduplicação ou limpeza antes da Bronze.
O diretório auxiliar é selecionado pelos municípios do recorte.

Esses microdados são privados no fluxo de trabalho: nunca publicar CSV/ZIP no GitHub,
compartilhar em capturas ou incluí-los no vídeo. Use o diretório ignorado `data/official-raw`
e o bucket privado do laboratório. Não use `git add -f`. O manifesto guarda consultas,
contagens, hashes e IDs de jobs, mas não valores individuais dos alunos.

O pacote antigo `dados-oficiais-2024.zip` contém alunos agregados e não atende à nova
Bronze bruta. Ele permanece como evidência da versão anterior; não foi apagado nem alterado.

## Estimativa e extração no notebook

Na raiz do projeto, com Python, biblioteca BigQuery e autenticação ADC:

```powershell
python -m pip install -e ".[gcp]"
gcloud auth application-default login
python scripts/extract_official_data.py --billing-project SEU_PROJETO_GCP --year 2024 --output data/official-raw
```

O padrão é somente dry run, com limite de 1 GiB por consulta. A consulta bruta pode
ler mais bytes que a agregada antiga. Revise a nova estimativa: não aumente o limite
automaticamente nem use os 193 MB da versão anterior como previsão da nova extração.

Após revisão explícita, acrescente `--execute`. O destino precisa estar vazio.
O manifesto só é gravado quando as sete consultas terminam. Uma extração incompleta
não pode ser empacotada/publicada como snapshot válido. Não é preciso ligar a AWS.

## Processamento após a Bronze

```powershell
python -m alfabetizacao_pipeline.cli batch-official --source-dir data/official-raw --output work-validation-raw
python scripts/validate_official_outputs.py --source-dir data/official-raw --output work-validation-raw
```

O processo local primeiro copia os extratos para `bronze/oficial/ingestao=<id>/`.
Na AWS, eles já estão no snapshot Bronze privado antes da invocação da Lambda.
Somente então o processamento de alunos:

1. Lê o CSV sequencialmente, sem carregar todos os alunos na RAM.
2. Seleciona presença `1`, caderno preenchido `1` e alfabetizado `0` ou `1`.
3. Conta pares distintos `(id_escola, id_aluno)` não vazios por ano/município,
   usando SQLite temporário em disco; exclui os temporários ao terminar.
4. Integra apenas as contagens aos resultados/metas. Silver/Gold não carregam IDs individuais.

Os contadores distinguem registros originais, avaliações válidas/inválidas e IDs ausentes.
`source_rows.alunos` passa a contar linhas brutas; `student_aggregate_rows` informa grupos
municipais. A execução real de 30/08/2026 confirmou 1.840.277 linhas brutas,
5.452 grupos e as mesmas contagens finais da versão anterior; ver
[validação bruta AWS](validacao-bruta-aws.md).

## Qualidade, limites e interpretação

Chaves duplicadas de referência, fonte vazia ou recorte errado interrompem a integração.
Metas/resultados ausentes, percentuais inválidos e relações faltantes são registrados
na quarentena por município. A reconciliação esperada é entrada = Silver + excluídos.
O batch AWS não substitui a Gold anterior quando nenhum município é aprovado.

Na demonstração anterior, 5.448 entradas resultaram em 5.232 aprovados e 216 excluídos:
96 sem registro de meta, 120 com meta de 2024 vazia. Esses números são referência de
regressão. A nova execução bruta na AWS reproduziu essas contagens conforme o relatório
acima; as evidências antigas continuam identificadas como históricas.

A média ponderada por alunos avaliados não reproduz a ponderação amostral do ICA oficial
da UF. Os indicadores oficiais da rede pública são mantidos separadamente na Silver/ranking.
As análises descrevem somente o recorte com dados completos, não todo o Brasil.

O modo local legado aceita `alunos_agregados.csv` para auditar os artefatos antigos.
Extração, pacote e upload novos exigem `alunos.csv` bruto. Consulte
[transferência e snapshots](transferencia-dados-oficiais.md).
