# Implantação no AWS Academy Learner Lab

A implantação usa somente `us-east-1` e evita EC2, EMR, Redshift e NAT Gateway. Os
recursos são S3, Lambda, Kinesis, Glue Data Catalog, Athena e CloudWatch.

## Antes de iniciar

1. Inicie o Learner Lab e espere o indicador ficar verde.
2. Abra o Console pelo link AWS do laboratório.
3. Abra o CloudShell e confirme `aws sts get-caller-identity`.
4. Confira que a região é `us-east-1` e que o saldo não sofreu alteração inesperada.

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

## Executar o batch

```bash
FUNCTION=$(terraform output -raw batch_function)
aws lambda invoke --function-name "$FUNCTION" --payload '{}' --cli-binary-format raw-in-base64-out batch-result.json
cat batch-result.json
```

O resultado esperado contém `status: success`, nove entradas e zero erro de qualidade.

## Demonstrar streaming

Na raiz do projeto, com `boto3` disponível:

```bash
STREAM=$(terraform -chdir=infra/terraform output -raw kinesis_stream)
python scripts/publish_events.py --stream "$STREAM" --interval 1
```

Confira no S3 os prefixos `silver/stream/` e `quarantine/stream/` e os logs da Lambda
no CloudWatch.

## Evidências

Registre capturas do saldo, recursos do stack, execução da Lambda, objetos Bronze/Silver/Gold,
consulta no Athena e logs do CloudWatch. Não exponha Account ID, e-mail ou credenciais.

## Encerrar com segurança

```bash
cd infra/terraform
terraform destroy
```

Confirme a remoção das Lambdas, stream Kinesis e bucket S3. Depois confira o saldo e clique
em `End Lab`.
