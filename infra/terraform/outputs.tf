output "data_bucket" { value = aws_s3_bucket.data.id }
output "batch_function" { value = aws_lambda_function.batch.function_name }
output "stream_function" { value = aws_lambda_function.stream.function_name }
output "kinesis_stream" { value = aws_kinesis_stream.indicators.name }
output "athena_workgroup" { value = aws_athena_workgroup.analytics.name }
output "glue_database" { value = aws_glue_catalog_database.analytics.name }
