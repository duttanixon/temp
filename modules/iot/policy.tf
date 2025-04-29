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


# Iam policy for IOT thing group and policy management from backend service

resource "aws_iam_policy" "iot_backend_policy" {

  name        = "${var.environment}-iot-backend-service-policy"
  description = "Policy for managing IoT thing groups and policies"


  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # Thing group permissions
          "iot:CreateThingGroup",
          "iot:DescribeThingGroup",
          "iot:UpdateThingGroup",
          "iot:DeleteThingGroup",
          "iot:ListThingGroups",
          "iot:ListThingGroupsForThing",
          "iot:AddThingToThingGroup",
          "iot:RemoveThingFromThingGroup",
          "iot:ListThingsInThingGroup",


          # Thing permissions
          "iot:CreateThing",
          "iot:UpdateThing",
          "iot:DeleteThing",
          "iot:ListThings",
          "iot:DescribeThing",

          # Policy permissions
          "iot:CreatePolicy",
          "iot:AttachPolicy",
          "iot:DetachPolicy",
          "iot:ListPolicies",
          "iot:ListPolicyVersions",
          "iot:GetPolicy",
          "iot:DeletePolicy",
          
          # Certificate permissions
          "iot:CreateKeysAndCertificate",
          "iot:DescribeCertificate",
          "iot:ListCertificates",
          "iot:UpdateCertificate",
          "iot:DeleteCertificate",
          
          # Allow attaching policies to thing groups
          "iot:AttachThingPrincipal",
          "iot:DetachThingPrincipal",
          "iot:AttachPrincipalPolicy",
          "iot:DetachPrincipalPolicy"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the platform admin user from the common module
resource "aws_iam_user_policy_attachment" "iot_admin_policy_attachment" {
  user       = var.platform_backend_user_name
  policy_arn = aws_iam_policy.iot_backend_policy.arn
}


# IAM policy for certificate bucket access
resource "aws_iam_policy" "certificate_bucket_access" {
  name        = "${var.environment}-certificate-bucket-access-policy"
  description = "Policy for accessing the IoT certificate S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject",
          "s3:GeneratePresignedUrl"
        ]
        Resource = [
          aws_s3_bucket.certificate_bucket.arn,
          "${aws_s3_bucket.certificate_bucket.arn}/*"
        ]
      }
    ]
  })
}

# Attach certificate bucket access policy to the backend service user
resource "aws_iam_user_policy_attachment" "certificate_bucket_access_attachment" {
  user       = var.platform_backend_user_name
  policy_arn = aws_iam_policy.certificate_bucket_access.arn
}