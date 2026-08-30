# Runbook operacional

## Escopo e pré-requisitos

Este manual descreve o protótipo AWS com S3, Lambda, Kinesis, Glue Data Catalog e Athena.
Os comandos são para o CloudShell, na raiz da cópia do projeto (por exemplo,
`$HOME/projeto-fiap`), com laboratório ativo e infraestrutura implantada.
Não é necessário reabrir o laboratório apenas para ler as evidências já salvas.

```bash
BUCKET=$(terraform -chdir=infra/terraform output -raw data_bucket)
FUNCTION=$(terraform -chdir=infra/terraform output -raw batch_function)
```

Confira os valores antes de qualquer escrita. O guia de
[implantação](implantacao-aws.md) descreve a criação e a invocação do batch.

## Batch falhou ou retornou quarentena

1. Conferir a resposta da invocação e o JSON retornado. `StatusCode: 200` sozinho não
   comprova processamento correto; verificar `FunctionError` e o conteúdo da resposta.
2. Consultar os logs da função:

```bash
aws logs tail "/aws/lambda/$FUNCTION" --since 30m --no-cli-pager
aws s3 ls "s3://$BUCKET/bronze/oficial/" --recursive
aws s3 cp "s3://$BUCKET/control/latest_official.json" -
aws s3 ls "s3://$BUCKET/manifests/"
aws s3 ls "s3://$BUCKET/quarantine/"
```

3. Conferir os sete CSVs (incluindo `alunos.csv` bruto) e `extraction_manifest.json`
   no snapshot apontado por `control/latest_official.json`. Usar o `run_id` da
   resposta para localizar `manifests/<run_id>.json` e
   `quarantine/quality_issues_<run_id>.jsonl`. Um erro antes da conclusão pode não gerar
   manifesto; nesse caso, começar pelos logs.
4. Revisar as regras e os municípios excluídos. Na execução oficial validada, 96 não
   tinham registro de meta e 120 tinham meta de 2024 vazia. Não inventar metas para
   eliminar a quarentena. `success_with_quarantine` exige revisão de cobertura.
5. Depois de corrigir uma causa real e preservar o estado anterior em backup, reexecutar
   conforme o guia de implantação. Conferir entrada = Silver + excluídos e os totais
   no Athena. Reexecuções sobrescrevem a Silver e Gold batch atuais.

## Streaming sem saída ou com registros rejeitados

```bash
aws s3 ls "s3://$BUCKET/silver/stream/" --recursive
aws s3 ls "s3://$BUCKET/bronze/stream/" --recursive
aws s3 ls "s3://$BUCKET/quarantine/stream/" --recursive
aws logs tail /aws/lambda/fiap-alfabetizacao-dev-stream --since 10m --no-cli-pager
```

O envelope Kinesis original é gravado em `bronze/stream/ingestao=<id>/event.json`
antes do parsing e das validações de domínio. O nome do log acima pressupõe o prefixo padrão.
Não publicar envelopes contendo dados pessoais. Ajustar o nome se a configuração for diferente.
Aguardar o processamento antes de republicar. Conferir também se o mapeamento Kinesis
para Lambda está habilitado. Rejeições de parsing são gravadas em arquivos JSONL na
quarentena; não existe uma tabela `alfabetizacao_silver.dead_letter` nesta implantação.
Erros de infraestrutura devem ser investigados nos logs. Não presumir que quarentena
vazia significa sucesso sem conferir a Silver.

O streaming demonstrado usa eventos simulados e não recalcula a Gold batch. Não há
deduplicação persistente por `event_id`; republicações podem duplicar registros. Corrigir
o produtor antes de um reenvio deliberado e registrar essa reexecução nas evidências.

## Gold desatualizada

1. Conferir o manifesto e os horários dos objetos `silver/indicadores.csv`,
   `gold/indicadores_uf/data.csv` e `gold/ranking_vulnerabilidade/data.csv`.
2. Confirmar que o batch terminou. A Lambda grava esses objetos sequencialmente, sem
   transação atômica: uma falha parcial pode deixar resultados de execuções diferentes.
3. Preservar os resultados anteriores e reexecutar o batch completo com fontes coerentes.
   A Gold AWS é calculada em Python; Athena consulta os arquivos, não os materializa.
4. Conferir no Athena a tabela `indicadores_uf`. Os totais da extração validada são
   24 UFs, 5.232 municípios e 1.568.597 alunos avaliados; outras extrações exigem nova revisão.

Os SQLs `01` a `04` da pasta `sql/` usam sintaxe BigQuery e não são comandos operacionais
para esta implantação Athena. Não executá-los no Athena para reparar a Gold.

## Armazenamento, backup e recuperação

Na AWS, cada upload usa `bronze/oficial/ingestao=<uuid>/`. O ponteiro em
`control/latest_official.json` só muda após o conjunto completo; falhas deixam snapshots
parciais não publicados e preservam o ponteiro anterior. O bucket possui versionamento.
Isso preserva histórico de ingestão, mas não implementa Object Lock: usuários autorizados
e `terraform destroy` podem apagar versões. Não editar manualmente um snapshot publicado.

A execução local mantém cópias Bronze por `ingestao=<run_id>`, mas isso não equivale
a imutabilidade garantida. Na AWS, manifestos e quarentena batch têm o `run_id` no nome;
os CSVs batch Silver/Gold atuais usam chaves fixas, mas uma cópia de cada execução
fica em `runs/<run_id>/`. O manifesto não é uma cópia dos dados.

Antes de substituir extratos ou destruir recursos, baixar os arquivos necessários,
preservar os pacotes oficiais e salvar as capturas. O ZIP de resultados da demonstração
contém Silver, Gold, manifestos e quarentena, mas não os logs CloudWatch nem a Bronze.
Na versão atual, os extratos brutos são preservados separadamente no pacote privado
`dados-oficiais-brutos-2024.zip`. Antes de remover a nova infraestrutura, salvar também
os snapshots Bronze, `runs/` e `control/`; não publicar esses backups no Git.

Não existe rollback automático por views. Para reconstruir uma versão anterior, é
necessário um snapshot histórico (ou backup) daquela extração e a versão correspondente do código, seguido
de reprocessamento e validação. Sem backup, não há recuperação de objetos sobrescritos
ou apagados garantida pelo projeto. As versões S3 também são eliminadas no destroy.

## Batch mensal

A regra `fiap-alfabetizacao-dev-batch-monthly` executa no dia 1 às 06:00 UTC.
`enable_monthly_batch` é `false` por padrão. Após publicar e validar um snapshot bruto,
habilitar a variável em `terraform.tfvars`, gerar plano novo e revisar antes de aplicar.
O job reprocessa o último snapshot; não consulta BigQuery nem obtém dados novos sozinho.
Uma nova extração deve ser publicada para a próxima execução consumir nova fonte.

Para demonstrar o agendamento sem aguardar um mês, conferir regra, alvo e permissão,
e testar o mesmo payload manualmente. A comprovação de um disparo temporal exige uma
execução real agendada; não apresentar uma invocação manual como prova desse disparo.
Nunca deixar agendamento habilitado depois da demonstração. Em caso de AccessDenied
no Academy, guardar o erro e consultar as permissões do professor, sem criar roles alternativas.

## Encerramento e controle de custos

1. Conferir o indicador de consumo do Learner Lab; não concluir que a execução foi
   gratuita apenas porque o painel ainda mostra zero.
2. Salvar resultados, logs necessários e prints antes da remoção.
3. Gerar um plano de destruição, revisar os alvos e só então aplicá-lo, conforme o guia
   de implantação. O bucket tem `force_destroy = true`: seu conteúdo também será apagado.
4. Conferir a conclusão e `terraform -chdir=infra/terraform state list` vazio.
5. Salvar a evidência de encerramento e executar End Lab. Estado vazio comprova apenas
   ausência de recursos gerenciados naquele estado, não uma auditoria de toda a conta.
