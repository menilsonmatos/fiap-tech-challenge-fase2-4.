# Registro de decisões arquiteturais

## ADR-001 — AWS Academy Learner Lab

**Decisão:** AWS em `us-east-1`, aproveitando o ambiente acadêmico com US$ 50.

**Consequência:** serviços e permissões são restritos; a execução local continua disponível.

## ADR-002 — S3 como Arquitetura Medalhão

**Decisão:** um bucket privado com prefixos Bronze, Silver, Gold e quarentena.

**Motivação:** baixo custo, simplicidade e separação lógica suficiente para a demonstração.

## ADR-003 — Lambda no processamento

**Decisão:** Lambda para batch e consumidor Kinesis.

**Trade-off:** Glue/EMR seriam mais adequados a volumes muito grandes, mas custariam mais e
adicionariam complexidade desnecessária ao volume do protótipo.

## ADR-004 — Athena e Glue Data Catalog

**Decisão:** consulta serverless sobre dados no S3, com limite de bytes por consulta.

**Motivação:** demonstrar warehouse/lake analytics sem manter cluster provisionado.
