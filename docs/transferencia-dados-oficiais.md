# Pacote local para transferência à AWS

Pacote preparado em 30/08/2026: `dist/dados-oficiais-2024.zip`.
Tamanho: 353.733 bytes. Contém somente sete CSVs e `extraction_manifest.json`,
sob o diretório `data/official/`. Não contém código, credenciais, Terraform state
nem identificadores individuais nas colunas dos CSVs.

SHA-256 do pacote preparado:

```text
8aa1d2c8379bb285d0ce06afc34fb42540b0896aa64037e428472462aa9d032f
```

Foram conferidos os hashes e contagens dos CSVs contra o manifesto, os cabeçalhos
e a integridade de cada arquivo dentro do ZIP. A pasta `dist/` é ignorada pelo Git.
O pacote ainda não foi enviado à AWS.

## Recriar localmente

Na raiz do projeto, no PowerShell:

```powershell
python scripts/package_official_sources.py --output dist/dados-oficiais-2024-novo.zip
```

O script recusa sobrescrever arquivos existentes. Um novo ZIP pode ter outro hash
por causa dos metadados da compactação; use o hash exibido para aquele pacote.

## Após transferir o ZIP para o CloudShell

Os comandos abaixo pressupõem o arquivo em `$HOME/dados-oficiais-2024.zip` e a cópia
do projeto em `$HOME/projeto-fiap`. Confira esses caminhos antes de continuar.
Na cópia do projeto, use a versão da branch `feature/integracao-dados-oficiais`
ou a versão correspondente já integrada à principal. Não descarte mudanças locais.

```bash
sha256sum "$HOME/dados-oficiais-2024.zip"
unzip -l "$HOME/dados-oficiais-2024.zip"
```

Compare o hash com o informado acima. Devem existir exatamente oito arquivos sob
`data/official/`. Se hash ou conteúdo diferirem, pare e confira a transferência.

Para não misturar extrações antigas, descompacte em um diretório temporário novo:

```bash
TRANSFER_DIR=$(mktemp -d "$HOME/fiap-oficial-XXXXXX")
unzip "$HOME/dados-oficiais-2024.zip" -d "$TRANSFER_DIR"
```

Somente depois da implantação e confirmação do bucket do projeto, na raiz do repositório:

```bash
cd "$HOME/projeto-fiap"
BUCKET=$(terraform -chdir=infra/terraform output -raw data_bucket)
PYTHONPATH=src python3 scripts/upload_official_sources.py --bucket "$BUCKET" --source-dir "$TRANSFER_DIR/data/official"
```

Esse último comando escreve no S3 e substitui objetos existentes em `bronze/oficial/`.
Ele deve ser executado apenas no bucket confirmado do projeto. A extração no BigQuery
não precisa ser repetida. Continue pelo guia de [implantação AWS](implantacao-aws.md).
