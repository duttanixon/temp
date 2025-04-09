resource "aws_iot_policy" "device_policy" {
    name = "${var.environment}-DeviceCommunicationPolicy"

    # The policy document defines what actions are allowed or denied
    # This uses IoT policy variables to dynamically restrict access based on the connecting certificates

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "iot:Connect"
                ]
            Resource = [
                # ${iot:ClientId} must match ${iot:CertificateID} for secure device identification
                "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:client/*"
            ]
            },
            {
                Effect = "Allow"
                Action = [
                    "iot:Publish"
                ]
                Resource = [
                    # Allow devices to publish data based on their certificate ID
                    "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:topic/devices/$${iot:ClientId}/data/*",
                    # Allow devices to publish their status
                    "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:topic/devices/$${iot:ClientId}/status"
                ]

            },
            {
                Effect = "Allow"
                Action = [
                    "iot:Subscribe"
                    ]
                Resource = [
                # Allow devices to subscribe to commands from the cloud
                "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:topicfilter/devices/$${iot:ClientId}/commands"
                ]
            },
            {
            Effect = "Allow"
            Action = [
                "iot:Receive"
                ]
            Resource = [
                # Allow devices to receive commands from the cloud
                "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:topic/devices/$${iot:ClientId}/commands"
                ]
            }

        ]
    })
}