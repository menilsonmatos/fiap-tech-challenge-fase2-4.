# FinOps

O orçamento do AWS Academy Learner Lab é limitado e compartilhado ao longo do curso.

Controles adotados:

1. Região única `us-east-1`.
2. Lambda com 128–256 MiB e timeout máximo de 60 segundos.
3. Um shard Kinesis, mantido somente durante a demonstração.
4. CloudWatch Logs com retenção de sete dias.
5. S3 privado e sem versionamento para evitar cópias desnecessárias no protótipo.
6. Athena com corte automático em 1 GiB lido por consulta.
7. Proibição arquitetural de EC2, EMR, Redshift e NAT Gateway nesta entrega.
8. `terraform destroy` obrigatório ao final da captura de evidências.

Antes e depois de cada sessão, registre o indicador `Used $X of $50` do Learner Lab. Pare
a implantação se houver consumo inesperado e consulte o CloudWatch e os recursos ativos.
