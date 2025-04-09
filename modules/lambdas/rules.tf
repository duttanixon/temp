# IoT Rules that trigger lambda functions

resource "aws_iot_topic_rule" "lambda_trigger_rules" {
    for_each = local.iot_rules

    name            = each.value.name
    description     = each.value.description
    enabled         = true

    sql             = each.value.sql
    sql_version     = "2016-03-23"

    lambda {
        function_arn =  aws_lambda_function.iot_data_processor_functions[each.value.lambda_key].arn
    }

}

# Permission to allow IoT to invoke the Lambda functions
resource "aws_lambda_permission" "allow_iot_invocations" {
    for_each        = local.iot_rules
    statement_id    = "AllowExecutionFromIoT_${each.key}"
    action          = "lambda:InvokeFunction"
    function_name   = aws_lambda_function.iot_data_processor_functions[each.value.lambda_key].function_name
    principal       = "iot.amazonaws.com"
    source_arn      =  aws_iot_topic_rule.lambda_trigger_rules[each.key].arn
}