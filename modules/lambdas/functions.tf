# Lambda functions  and related resources
resource "aws_lambda_function" "iot_data_processor_functions" {
    for_each = local.lambda_functions

    function_name       = each.value.function_name
    description         = each.value.description
    role                = aws_iam_role.lambda_execution_role.arn
    runtime             = each.value.runtime
    handler             = each.value.handler
    filename            = data.archive_file.lambda_archives[each.key].output_path
    source_code_hash    = data.archive_file.lambda_archives[each.key].output_base64sha256

    dynamic "environment" {
        for_each = length(each.value.environment_variables) > 0 ? [1] : []
        content {
            variables = each.value.environment_variables
        }
    }
}