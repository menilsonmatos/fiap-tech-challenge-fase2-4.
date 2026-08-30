# Implantação no AWS Academy Learner Lab

A implantação usa somente `us-east-1` e evita EC2, EMR, Redshift e NAT Gateway. Os
recursos são S3, Lambda, Kinesis, Glue Data Catalog, Athena e CloudWatch.

## Antes de iniciar

Prepare os extratos e o ZIP local antes de ligar o laboratório, conforme
[transferencia-dados-oficiais.md](transferencia-dados-oficiais.md).

1. Inicie o Learner Lab e espere o indicador ficar verde.
2. Abra o Console pelo link AWS do laboratório.
3. Abra o CloudShell e confirme `aws sts get-caller-identity`.
4. Confira que a região é `us-east-1` e que o saldo não sofreu alteração inesperada.
5. Transfira os extratos brutos já preparados conforme `docs/dados-oficiais.md`,
   para o ambiente usado na implantação. Não envie esse diretório ao GitHub.

## Implantar

No CloudShell, disponibilize o repositório. Os comandos abaixo pressupõem a cópia em
`$HOME/projeto-fiap` e são executados a partir da raiz. Ajuste o caminho se necessário.
Prepare `terraform.tfvars` a partir do exemplo somente se ainda não existir;
não sobrescreva uma configuração anterior sem revisá-la.

```bash
cd "$HOME/projeto-fiap"
test -f infra/terraform/terraform.tfvars || cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan -out=tfplan-oficial
```

Revise os recursos planejados antes de executar (cria recursos e pode consumir créditos):

```bash
terraform -chdir=infra/terraform apply tfplan-oficial
```

Se o CloudShell não possuir Terraform, instale uma versão oficial no diretório do usuário
ou use o binário indicado pelo professor. Não exporte credenciais do Learner Lab.

## Enviar as fontes oficiais para a Bronze

Na raiz do projeto:

```bash
BUCKET=$(terraform -chdir=infra/terraform output -raw data_bucket)
PYTHONPATH=src python3 scripts/upload_official_sources.py \
  --bucket "$BUCKET" \
  --source-dir data/official-raw
```

## Executar o batch oficial

Permaneça na raiz do projeto. Aguarde a conclusão do upload dos oito arquivos.
Cada upload cria `bronze/oficial/ingestao=<uuid>/` e publica o ponteiro ao final.
Se usou o pacote transferido, informe o caminho `$TRANSFER_DIR/data/official` no upload.
O batch preserva resultados em `runs/<run_id>/` e atualiza os CSVs Silver/Gold atuais.

```bash
FUNCTION=$(terraform -chdir=infra/terraform output -raw batch_function)
aws lambda invoke --function-name "$FUNCTION" --payload '{}' --cli-binary-format raw-in-base64-out --cli-read-timeout 930 --no-cli-pager batch-result.json
cat batch-result.json
```

O evento vazio resolve `control/latest_official.json` para ler um snapshot completo.
O resultado esperado
contém `source` igual à Base dos Dados, volumes por entidade e balanço entre municípios
recebidos, publicados e excluídos. `source_rows.alunos` agora conta linhas brutas;
`student_aggregate_rows` conta os grupos municipais. IDs individuais ficam somente
na Bronze privada, não na Silver/Gold. O status pode ser `success_with_quarantine` quando as fontes têm cobertura
diferente; revise as ocorrências antes de aceitar o resultado.

## Demonstrar streaming

Verifique também os envelopes originais em `bronze/stream/`, antes de aceitar a evidência.

Na raiz do projeto, com `boto3` disponível:

```bash
STREAM=$(terraform -chdir=infra/terraform output -raw kinesis_stream)
python3 scripts/publish_events.py --stream "$STREAM" --interval 1
```

Confira no S3 os prefixos `silver/stream/` e `quarantine/stream/` e os logs da Lambda
no CloudWatch.

Esses eventos são simulados e ficam separados da Silver batch; não atualizam a Gold.

## Evidências

Além do fluxo anterior, comprove dois snapshots Bronze preservados, versionamento do
bucket, envelope bruto de streaming e a regra mensal (desativada por padrão).
Não usar os prints anteriores para afirmar que essas novas funções já foram validadas.

## Agendamento mensal

O Terraform cria regra EventBridge, alvo Lambda e permissão de invocação, sem nova IAM role.
A regra é `cron(0 6 1 * ? *)` (dia 1, 06:00 UTC), desativada por padrão.
Após upload completo e teste manual, ativar `enable_monthly_batch = true` em
`terraform.tfvars` somente se houver intenção de manter o laboratório em execução.
A aquisição de novos extratos BigQuery continua manual; a regra processa o snapshot
completo mais recente. Não deixar recursos ativos esperando um mês para gravar o vídeo.
Para a demonstração, registre a configuração e identifique honestamente que o teste
manual não comprova um disparo temporal. Permissões EventBridge ainda precisam ser
confirmadas neste Learner Lab.

Registre capturas do saldo, recursos do stack, manifesto com a fonte oficial, objetos das
seis entidades na Bronze, Silver/Gold, consulta no Athena e logs do CloudWatch. Não exponha
Account ID, e-mail, credenciais ou identificadores de alunos.

## Encerrar com segurança

Primeiro salve os prints, baixe os resultados e confira o backup no notebook. Preserve
também os logs necessários; eles serão removidos. Na raiz do projeto, gere o plano:

```bash
terraform -chdir=infra/terraform plan -destroy -out=tfplan-encerramento
```

Revise o plano. A aplicação abaixo apaga os recursos planejados e o conteúdo do bucket:

```bash
terraform -chdir=infra/terraform apply tfplan-encerramento
terraform -chdir=infra/terraform state list
```

Confirme a remoção das Lambdas, stream Kinesis e bucket S3. Depois confira o saldo e clique
em `End Lab`.
