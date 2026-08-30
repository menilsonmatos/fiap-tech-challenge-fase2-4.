# Transferência privada e snapshots completos

## Preparar no notebook

Depois da nova extração bruta completa e validação local:

```powershell
python scripts/package_official_sources.py --source-dir data/official-raw --output dist/dados-oficiais-brutos-2024.zip
```

O script verifica hashes e contagens contra `extraction_manifest.json` e inclui exatamente
sete CSVs e o manifesto. O ZIP contém microdados de alunos: manter privado, fora do Git.
O script imprime tamanho e SHA-256; guardar esse hash para conferir a transferência.
Não sobrescreve pacotes existentes. O antigo ZIP agregado não pode ser reutilizado.

## Transferir ao CloudShell

Faça upload manual pelo menu Actions do CloudShell. Na sessão, confira o hash e extraia
em diretório novo. Não publique o pacote em links públicos.

```bash
sha256sum "$HOME/dados-oficiais-brutos-2024.zip"
TRANSFER_DIR=$(mktemp -d "$HOME/fiap-bruto-XXXXXX")
unzip "$HOME/dados-oficiais-brutos-2024.zip" -d "$TRANSFER_DIR"
```

O hash deve ser igual ao impresso no notebook. Após implantar a infraestrutura e confirmar
o bucket, na raiz da cópia atualizada do projeto:

```bash
cd "$HOME/projeto-fiap"
BUCKET=$(terraform -chdir=infra/terraform output -raw data_bucket)
PYTHONPATH=src python3 scripts/upload_official_sources.py --bucket "$BUCKET" --source-dir "$TRANSFER_DIR/data/official"
```

## Protocolo de publicação

- Cada upload usa `bronze/oficial/ingestao=<uuid>/`, nunca substitui a ingestão anterior.
- Hashes e contagens são conferidos antes da transferência.
- Somente após os oito arquivos serem enviados, o script grava `control/latest_official.json`.
- Esse ponteiro contém o prefixo e o hash do manifesto. Uma falha parcial não publica
  o conjunto incompleto; os objetos parciais permanecem, sem serem consumidos pelo batch.
- A Lambda resolve o ponteiro uma única vez e confere novamente o manifesto e os CSVs.
  Assim, trocar o ponteiro durante uma execução não mistura duas extrações.
- O bucket tem versionamento. Preserva alterações do ponteiro e projeções Silver/Gold;
  não há Object Lock e `terraform destroy` continua sendo destrutivo.

O batch manual e mensal usam o último snapshot publicado. Para reprocessar um snapshot
anterior, a Lambda aceita `snapshot` com `prefix` e `manifest_sha256` conhecidos do
registro daquela ingestão. Não alterar os arquivos antigos para simular uma nova fonte.

Antes de destruir a infraestrutura, baixe todo o histórico necessário: `bronze/`,
`control/`, `runs/`, `manifests/`, `quarantine/`, Silver e Gold. Esses backups da Bronze
agora contêm microdados e não devem ser incluídos no repositório público.
