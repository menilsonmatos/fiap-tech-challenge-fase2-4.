# Demonstração local

O fluxo prioritário usa os extratos reais da Base dos Dados. Consulte
`docs/dados-oficiais.md` e execute `batch-official`. O comando abaixo é uma validação
técnica offline com fixtures sintéticas e não produz indicadores oficiais.

Esta é a forma de validar o projeto sem depender da sessão do AWS Academy.
A demonstração executa o pipeline batch, simula o streaming e materializa localmente as
camadas Bronze, Silver e Gold. O Terraform e os módulos de nuvem permanecem no repositório
como arquitetura pronta para implantação, mas não precisam ser aplicados.

## Pré-requisito

- Windows com Python 3.11 ou superior.

## Execução em um comando

Abra o PowerShell nesta pasta e execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\demo-local.ps1
```

O script usa somente a biblioteca padrão do Python, executa todos os testes e roda as
duas modalidades do pipeline. Não precisa de internet, `pip`, conta de nuvem ou credencial.

## O que mostrar durante a apresentação

1. O terminal com todos os testes aprovados.
2. O manifesto em `demo-output/manifests`, que registra volume, qualidade e status.
3. A cópia bruta em `demo-output/bronze`.
4. Os dados validados em `demo-output/silver/indicadores.csv`.
5. Os indicadores estaduais em `demo-output/gold/indicadores_uf.csv`.
6. O ranking municipal em `demo-output/gold/ranking_vulnerabilidade.csv`.
7. A simulação de eventos em `demo-output/silver/stream_updates.jsonl`.
8. O diagrama e as decisões de produção no `README.md`.

## Observação para a banca

Os registros usados na demonstração são uma fixture sintética e reproduzível. A extração
da fonte oficial está implementada em `sql/00_source_basedosdados.sql`; sua execução direta
depende do acesso de consulta à Base dos Dados. Assim, a apresentação comprova localmente a
lógica, a qualidade, a rastreabilidade e as camadas do pipeline sem gerar custos de nuvem.
