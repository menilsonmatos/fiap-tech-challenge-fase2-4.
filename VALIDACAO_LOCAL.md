# Evidência de validação local

As evidências abaixo pertencem à versão anterior. A revisão para histórico Bronze,
alunos brutos e batch mensal está descrita em [aderência obrigatória](docs/aderencia-obrigatoria.md).
As capturas AWS antigas não validam as novas funcionalidades.

## Validação técnica com fixtures

Testes executados localmente, sem consultar serviços de nuvem.

- 35 testes executados e aprovados, incluindo filtros oficiais e o handler AWS Lambda.
- 9 registros recebidos no batch.
- 9 registros publicados na Silver.
- 0 erro e 0 aviso de qualidade.
- 3 eventos de streaming aceitos.
- 0 evento de streaming rejeitado.
- Camadas Bronze, Silver e Gold geradas em `demo-output`.

O manifesto JSON de execução está em `demo-output/manifests` e permite conferir o
`run_id`, a origem, a cópia Bronze, os volumes e o status `success`.

Os números acima pertencem à fixture técnica original. Os testes de integração oficial
usam arquivos mínimos com o mesmo esquema público, em `tests/fixtures/official`, mas não
substituem a execução final com os extratos reais em `data/official`.

Os testes da extração usam um cliente BigQuery simulado para verificar dry run,
limites de bytes e geração do manifesto. São distintos da extração real abaixo.

## Validação com dados oficiais — 30/08/2026

A extração autenticada no BigQuery foi concluída pelo usuário, seguida de processamento
local. A auditoria dos arquivos locais passou. Veja o relatório completo em
[docs/validacao-dados-oficiais.md](docs/validacao-dados-oficiais.md).

- Execução: `20260830T163220Z`, ano de referência 2024.
- 5.448 municípios recebidos; 5.232 aprovados e 216 em quarentena.
- 96 sem registro correspondente de meta municipal; 120 com meta de 2024 vazia.
- Ranking: 5.232 municípios. Gold por UF: 24 linhas.
- Total de alunos avaliados no recorte aprovado: 1.568.597.
- Status do pipeline: `success_with_quarantine`; status da auditoria: `passed`.
- 35 testes automatizados executados novamente e aprovados.

A execução AWS oficial `20260830T174218Z` reproduziu as contagens locais. O Athena
confirmou 24 UFs, 5.232 municípios e 1.568.597 alunos avaliados. Isso confere os totais,
não uma comparação linha a linha entre resultados locais e AWS.
As [evidências atuais](docs/evidencias/README.md) distinguem o batch oficial do streaming
simulado. Os 12 recursos gerenciados foram removidos e o estado ficou vazio.
