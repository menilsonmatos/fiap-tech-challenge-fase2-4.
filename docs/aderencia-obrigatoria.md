# Revisão dos requisitos obrigatórios

Branch: `feature/aderencia-medalhao-obrigatoria`. Nenhum recurso de nuvem foi criado
durante a implementação. Não foram adicionados dashboard, ML treinado, enriquecimento
externo ou observabilidade avançada.

| Requisito | Implementação | Evidência ainda necessária |
|---|---|---|
| Histórico Bronze | Snapshots batch por UUID, ponteiro de conjunto completo e bucket versionado | Dois uploads preservados no S3 e versionamento Enabled |
| Dados brutos | `SELECT *` para alunos do recorte, CSV intacto na Bronze, agregação posterior em SQLite | Nova extração bruta real e medição de disco/tempo na Lambda |
| Bronze streaming | Envelope Kinesis completo salvo antes de parsing/qualidade | Evento na Bronze e resultado Silver/quarentena correlacionado |
| Batch periódico | EventBridge mensal, alvo e permissão Lambda; desativado por padrão | Permissões do Lab e configuração/disparo quando autorizado |
| FinOps | Premissas monetárias, fórmulas, tarifas e limites em `finops.md` | Recalcular com tamanho/tempo reais e conferir saldo |
| README | Contexto educacional, trade-offs, fluxo da Gold para Athena e limites | Revisão final após nova validação |

## Testes locais

Em 30/08/2026, os 48 testes passaram. `terraform fmt -check` e
`terraform validate` também passaram (Terraform 1.9.8, AWS 5.100.0 e Archive 2.8.0).
A validação usou binários oficiais com SHA-256 conferido e `dev_overrides` local,
pois o ambiente bloqueou a instalação normal dos providers. O aviso de overrides
é esperado; não houve plano, aplicação ou validação de permissões na AWS.

Testes automatizados cobrem a integridade do snapshot, falha de upload sem trocar o
ponteiro, leitura consistente pelo batch, preservação de duas ingestões e de execuções,
regra de elegibilidade de alunos, duplicidades, IDs ausentes, ausência de IDs na Silver,
arquivo bruto mantido intacto, pacote com lista restrita de arquivos e streaming bruto
arquivado antes de aceitar/rejeitar eventos. O cliente S3 é simulado; isso não comprova
permissões reais do Learner Lab. Os testes de Terraform em Python são estruturais.

## Migração segura

1. Manter os extratos, ZIPs e prints anteriores como histórico.
2. Rodar somente o dry run da extração nova para `data/official-raw`; revisar bytes.
3. Autorizar a execução real, validar o batch local e comparar indicadores/contagens
   com os anteriores. Agora `source_rows.alunos` conta alunos brutos, não grupos.
4. Empacotar em ZIP privado novo; nunca publicar microdados ou IDs no Git.
5. Só então reabrir o Lab, executar init/validate e revisar o plano. Não usar planos antigos.
6. Publicar snapshot, executar batch, conferir Athena, histórico de duas ingestões,
   Bronze streaming e regra mensal. Não alegar disparo automático usando só teste manual.
7. Salvar novas evidências e backups privados, revisar o plano de destruição e encerrar.

## Limites explícitos

A regra mensal processa o snapshot mais recente publicado, não extrai BigQuery. O
download de fonte externa permanece autenticado/manual. A configuração mensal não
garante que o Academy mantenha a sessão e permissões por um mês; precisa ser validada.

O recorte bruto pode ser grande. A Lambda tem 900 s, 1 GiB RAM e 4 GiB temporários;
se ultrapassar esses limites, a demonstração deve parar para ajuste, não truncar alunos.
Os resultados históricos guardam todas as execuções; as projeções Silver/Gold atuais
ainda são escritas sequencialmente, sem transação atômica. Eventos podem ser repetidos
pelo serviço: não há deduplicação persistente de streaming. O versionamento não impede
remoção administrativa; preserve backup antes do destroy, que também apaga versões.
