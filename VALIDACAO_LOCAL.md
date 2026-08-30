# Evidência de validação local

Validação executada sem cloud e sem dependências externas.

- 19 testes executados e aprovados, incluindo integração oficial e o handler AWS Lambda.
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
