# Evidências atuais — 30/08/2026

## Revisão com Bronze bruta — execução das 19:53 UTC

| Evidência | O que comprova |
|---|---|
| [Implantação bruta](terraform_bruto_implantado.png) | 16 recursos criados sem alterações ou destruições |
| [Agendamento mensal](agendamento_mensal.png) | Regra DISABLED, cron mensal e alvo batch; não comprova disparo automático |
| [Batch bruto](batch_bruto_aws.png) | 1.840.277 linhas brutas, 5.452 grupos e 5.232 municípios Silver |
| [Athena bruto](athena_bruto_aws.png) | 24 UFs, 5.232 municípios, 1.568.597 avaliados |
| [Histórico versionado](bronze_historico_versionado.png) | Dois snapshots distintos e versionamento Enabled |
| [Streaming Bronze/Silver](streaming_bronze_silver.png) | Três publicações, dois envelopes e dois arquivos processados |
| [Resultado streaming](streaming_bruto_resultado.png) | Três registros simulados, não atualizações oficiais |
| [Desempenho batch](lambda_batch_bruto_desempenho.png) | 188,58 s e 356 MB máximos; disco não medido |
| [Encerramento bruto](encerramento_bruto_destroy.png) | 16 recursos destruídos e estado vazio |

As capturas de implantação e agendamento foram revisadas após ocultação do ID da conta.
A auditoria local foi apresentada na conversa, mas seu print
não foi encontrado nesta pasta na revisão. O [relatório](../validacao-bruta-aws.md)
registra os resultados, backup e limites da comprovação.

## Histórico anterior — alunos agregados na origem

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

## Infraestrutura e encerramento

As três capturas abaixo foram revisadas após o usuário ocultar o ID da conta e o e-mail.
Os nomes dos recursos, status e resultados foram preservados:

- [Lambda](lambda_atualizado.png): duas funções do projeto; as demais funções visíveis pertencem
  ao laboratório e não fazem parte da implementação do projeto.
- [Kinesis](kinesis_atualizado.png): stream do projeto com status Active.
- [Encerramento](encerramento_destroy.png): 12 recursos destruídos e estado do Terraform vazio.

O encerramento removeu a infraestrutura da demonstração; o código, os extratos locais
e o ZIP de resultados no notebook permanecem preservados. O usuário confirmou ter
executado End Lab após a remoção. Essa confirmação não é uma captura do painel;
o consumo final de créditos não foi verificado.

## Evidências históricas

Os demais prints anteriores desta pasta registram testes com a amostra sintética inicial.
São mantidos como histórico, não como comprovação do batch oficial de 5.232 municípios.
