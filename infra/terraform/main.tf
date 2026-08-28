data "aws_caller_identity" "current" {}

locals {
  prefix = "${var.project_name}-${var.environment}"
  tags = { Project = "Tech Challenge Fase 2", Environment = var.environment, ManagedBy = "Terraform" }
}

resource "aws_s3_bucket" "data" {
  bucket        = "${local.prefix}-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
  tags          = local.tags
}
resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }
}
resource "aws_s3_object" "sample" {
  bucket = aws_s3_bucket.data.id
  key = "bronze/indicador_alfabetizacao.csv"
  source = "${path.module}/../../data/source/indicador_alfabetizacao.csv"
  etag = filemd5("${path.module}/../../data/source/indicador_alfabetizacao.csv")
  content_type = "text/csv"
}

data "archive_file" "lambda" {
  type = "zip"
  source_dir = "${path.module}/../../src"
  output_path = "${path.module}/lambda.zip"
}
resource "aws_iam_role" "lambda" {
  name = "${local.prefix}-lambda"
  assume_role_policy = jsonencode({Version="2012-10-17",Statement=[{Action="sts:AssumeRole",Effect="Allow",Principal={Service="lambda.amazonaws.com"}}]})
  tags = local.tags
}
resource "aws_iam_role_policy" "lambda" {
  name = "${local.prefix}-least-privilege"
  role = aws_iam_role.lambda.id
  policy = jsonencode({Version="2012-10-17",Statement=[
    {Effect="Allow",Action=["s3:GetObject","s3:PutObject"],Resource="${aws_s3_bucket.data.arn}/*"},
    {Effect="Allow",Action=["kinesis:GetRecords","kinesis:GetShardIterator","kinesis:DescribeStream","kinesis:ListShards"],Resource=aws_kinesis_stream.indicators.arn},
    {Effect="Allow",Action=["logs:CreateLogStream","logs:PutLogEvents"],Resource="arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.prefix}-*:*"}
  ]})
}
resource "aws_cloudwatch_log_group" "batch" {
  name              = "/aws/lambda/${local.prefix}-batch"
  retention_in_days = 7
  tags              = local.tags
}
resource "aws_cloudwatch_log_group" "stream" {
  name              = "/aws/lambda/${local.prefix}-stream"
  retention_in_days = 7
  tags              = local.tags
}
resource "aws_lambda_function" "batch" {
  function_name = "${local.prefix}-batch"
  role = aws_iam_role.lambda.arn
  handler = "alfabetizacao_pipeline.aws_handler.batch_handler"
  runtime = "python3.12"
  filename = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout = 60
  memory_size = 256
  environment { variables = { DATA_BUCKET = aws_s3_bucket.data.id } }
  depends_on = [aws_cloudwatch_log_group.batch]
  tags = local.tags
}

resource "aws_kinesis_stream" "indicators" {
  name = "${local.prefix}-indicadores"
  shard_count = 1
  retention_period = 24
  stream_mode_details { stream_mode = "PROVISIONED" }
  tags = local.tags
}
resource "aws_lambda_function" "stream" {
  function_name = "${local.prefix}-stream"
  role = aws_iam_role.lambda.arn
  handler = "alfabetizacao_pipeline.aws_handler.streaming_handler"
  runtime = "python3.12"
  filename = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout = 30
  memory_size = 128
  environment { variables = { DATA_BUCKET = aws_s3_bucket.data.id } }
  depends_on = [aws_cloudwatch_log_group.stream]
  tags = local.tags
}
resource "aws_lambda_event_source_mapping" "stream" {
  event_source_arn = aws_kinesis_stream.indicators.arn
  function_name = aws_lambda_function.stream.arn
  starting_position = "LATEST"
  batch_size = 10
}

resource "aws_glue_catalog_database" "analytics" { name = replace("${local.prefix}-analytics", "-", "_") }
resource "aws_glue_catalog_table" "gold_uf" {
  name          = "indicadores_uf"
  database_name = aws_glue_catalog_database.analytics.name
  table_type    = "EXTERNAL_TABLE"
  parameters    = { "skip.header.line.count" = "1", classification = "csv" }
  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data.id}/gold/indicadores_uf/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"
    ser_de_info { serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde" }
    columns { name = "ano", type = "int" }
    columns { name = "sigla_uf", type = "string" }
    columns { name = "percentual_alfabetizado_ponderado", type = "double" }
    columns { name = "meta_percentual_ponderada", type = "double" }
    columns { name = "gap_meta_pp", type = "double" }
    columns { name = "municipios", type = "int" }
    columns { name = "municipios_na_meta", type = "int" }
    columns { name = "total_avaliados", type = "bigint" }
  }
}
resource "aws_athena_workgroup" "analytics" {
  name = "${local.prefix}-analytics"
  configuration {
    enforce_workgroup_configuration = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query = 1073741824
    result_configuration { output_location = "s3://${aws_s3_bucket.data.id}/athena-results/" }
  }
  tags = local.tags
}
