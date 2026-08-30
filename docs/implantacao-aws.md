# Implantação no AWS Academy Learner Lab

A implantação usa somente `us-east-1` e evita EC2, EMR, Redshift e NAT Gateway. Os
recursos são S3, Lambda, Kinesis, Glue Data Catalog, Athena e CloudWatch.

## Antes de iniciar

1. Inicie o Learner Lab e espere o indicador ficar verde.
2. Abra o Console pelo link AWS do laboratório.
3. Abra o CloudShell e confirme `aws sts get-caller-identity`.
4. Confira que a região é `us-east-1` e que o saldo não sofreu alteração inesperada.
5. Extraia as fontes reais conforme `docs/dados-oficiais.md` e transfira `data/official`
   para o ambiente usado na implantação. Não envie esse diretório ao GitHub.

## Implantar

No CloudShell, disponibilize o repositório e execute:

```bash
cd fiap-tech-challenge-fase2/infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Se o CloudShell não possuir Terraform, instale uma versão oficial no diretório do usuário
ou use o binário indicado pelo professor. Não exporte credenciais do Learner Lab.

## Enviar as fontes oficiais para a Bronze

Na raiz do projeto:

```bash
BUCKET=$(terraform -chdir=infra/terraform output -raw data_bucket)
PYTHONPATH=src python scripts/upload_official_sources.py \
  --bucket "$BUCKET" \
  --source-dir data/official
```

## Executar o batch oficial

```bash
FUNCTION=$(terraform output -raw batch_function)
aws lambda invoke --function-name "$FUNCTION" --payload '{}' --cli-binary-format raw-in-base64-out batch-result.json
cat batch-result.json
```

O evento vazio usa, por padrão, os sete objetos em `bronze/oficial/`. O resultado esperado
contém `source` igual à Base dos Dados, volumes por entidade e balanço entre municípios
recebidos, publicados e excluídos. `alunos_agregados.csv` contém somente contagens, nunca
microdados. O status pode ser `success_with_quarantine` quando as fontes têm cobertura
diferente; revise as ocorrências antes de aceitar o resultado.

## Demonstrar streaming

Na raiz do projeto, com `boto3` disponível:

```bash
STREAM=$(terraform -chdir=infra/terraform output -raw kinesis_stream)
python scripts/publish_events.py --stream "$STREAM" --interval 1
```

Confira no S3 os prefixos `silver/stream/` e `quarantine/stream/` e os logs da Lambda
no CloudWatch.

## Evidências

Registre capturas do saldo, recursos do stack, manifesto com a fonte oficial, objetos das
seis entidades na Bronze, Silver/Gold, consulta no Athena e logs do CloudWatch. Não exponha
Account ID, e-mail, credenciais ou identificadores de alunos.

## Encerrar com segurança

```bash
cd infra/terraform
terraform destroy
```

Confirme a remoção das Lambdas, stream Kinesis e bucket S3. Depois confira o saldo e clique
em `End Lab`.
