resource "aws_iam_policy" "kinesis_video_streaming" {
  name        = "${var.environment}-kinesis_video_streaming"
  description = "Policy for devices to send video streams to Kinesis Video Streams"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kinesisvideo:CreateStream",
          "kinesisvideo:DescribeStream",
          "kinesisvideo:GetDataEndpoint",
          "kinesisvideo:PutMedia",
          "kinesisvideo:TagStream",
          "kinesisvideo:GetHLSStreamingSessionURL"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:kinesisvideo:${var.aws_region}:${data.aws_caller_identity.current.account_id}:stream/*",
          # Also allow actions on the service itself for operations like CreateStream
          "arn:aws:kinesisvideo:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        ]
      },
        {
            Effect = "Allow"
            Action = [
                "iot:Connect",
                "iot:Publish",
                "iot:Subscribe",
                "iot:Receive",

            ]
            Resource = "*"
        }
    ]
  })
}


# Attach s3 policy bucket access policy to the device service user
resource "aws_iam_user_policy_attachment" "kinesis_streaming_attachment_to_user" {
  user       = var.iot_device_metrics_user_name
  policy_arn = aws_iam_policy.kinesis_video_streaming.arn
}

resource "aws_iam_user_policy_attachment" "kinesis_streaming_to_backend_service" {
  user       = var.platform_backend_user_name
  policy_arn = aws_iam_policy.kinesis_video_streaming.arn
}
