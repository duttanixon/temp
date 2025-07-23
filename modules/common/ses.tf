# Create an SES domain identity for your domain
resource "aws_ses_domain_identity" "platform_domain" {
  domain = "cybercore.co.jp"
}

# Generate DKIM records to verify the domain and improve deliverability
resource "aws_ses_domain_dkim" "platform_domain_dkim" {
  domain = aws_ses_domain_identity.platform_domain.domain
}

# # IAM user specifically for sending emails via SES
# resource "aws_iam_user" "ses_user" {
#   name = "ses-smtp-user.20250723-2"
#   path = "/"

#   tags = {
#     Description = "User for sending emails via SES"
#     Environment = var.environment
#   }
# }

# # Create an access key for the SES user
# resource "aws_iam_access_key" "ses_user_key" {
#   user = aws_iam_user.ses_user.name
# }

# # IAM policy that grants permission to send emails
# resource "aws_iam_policy" "ses_send_email" {
#   name        = "${var.environment}-ses-send-email-policy"
#   description = "Allows sending emails via SES for a specific domain"

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow",
#         Action = [
#           "ses:SendEmail",
#           "ses:SendRawEmail"
#         ],
#         Resource = "*"
#       }
#     ]
#   })
# }

# # Attach the sending policy to the SES user
# resource "aws_iam_user_policy_attachment" "ses_user_policy_attachment" {
#   user       = aws_iam_user.ses_user.name
#   policy_arn = aws_iam_policy.ses_send_email.arn
# }


# Use the iam-user module to create the user and generate the SES SMTP password
module "ses_smtp_user" {
  source  = "xchan/iam/aws//modules/iam-user"
  version = "4.20.1"

  # --- Inputs for the module ---
  name = "${var.environment}-ses-smtp-user"
  path = "/service/"

  # This user is for programmatic access only, so no login profile is needed
  create_iam_user_login_profile = false

  # Note: We are not assigning any groups here.
  # Instead, we will attach a policy directly below.

  tags = {
    Description = "User for sending emails via SES SMTP"
    Environment = var.environment
  }
}

# IAM policy that grants permission to send emails
resource "aws_iam_policy" "ses_send_email" {
  name        = "${var.environment}-ses-send-email-policy"
  description = "Allows sending emails via SES"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ],
        Resource = "*" # Allows sending from any verified identity
      }
    ]
  })
}

# Attach the sending policy directly to the SES user
resource "aws_iam_user_policy_attachment" "ses_user_policy_attachment" {
  user       = module.ses_smtp_user.iam_user_name
  policy_arn = aws_iam_policy.ses_send_email.arn
}