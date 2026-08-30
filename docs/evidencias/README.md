# Evidências atuais — 30/08/2026

## Batch com dados oficiais

| Evidência | O que comprova |
|---|---|
| [Batch oficial](batch_oficial.png) | Fonte Base dos Dados/INEP; 5.448 entradas, 5.232 aprovados e 216 excluídos; execução `20260830T174218Z`. |
| [Athena oficial](athena_oficial.png) | Resultado agregado: 24 UFs, 5.232 municípios e 1.568.597 alunos avaliados. |
| [Bronze oficial no S3](s3_oficial.png) | Sete extratos CSV e o manifesto de extração. |

## Streaming simulado

[Registros processados do streaming](streaming_oficial.png): três eventos de demonstração,
referentes a Campinas, Fortaleza e Salvador. Apesar do nome do arquivo e do rótulo
`INEP/atualização`, os valores são **simulados**, não atualizações oficiais do INEP.
A captura mostra registros processados, não o manifesto do batch nem evidência de dados
oficiais em tempo real. O texto à direita está parcialmente cortado; os arquivos completos
foram preservados no backup baixado pelo usuário.

## Infraestrutura e encerramento — publicação pendente

As três capturas abaixo foram revisadas localmente, mas ainda não são incluídas no commit
porque exibem identificadores da conta e/ou e-mail. Antes de publicá-las, ocultar somente
esses identificadores, preservando nomes de recursos, status e resultados:

- `lambda_atualizado.png`: duas funções do projeto; as demais funções visíveis pertencem
  ao laboratório e não fazem parte da implementação do projeto.
- `kinesis_atualizado.png`: stream do projeto com status Active.
- `encerramento_destroy.png`: 12 recursos destruídos e estado do Terraform vazio.

O encerramento removeu a infraestrutura da demonstração; o código, os extratos locais
e o ZIP de resultados no notebook permanecem preservados. O status de End Lab e o
consumo final de créditos não são comprovados por essas capturas.

## Evidências históricas

Os demais prints anteriores desta pasta registram testes com a amostra sintética inicial.
São mantidos como histórico, não como comprovação do batch oficial de 5.232 municípios.
