terraform {
    backend "s3" {
        bucket = "cc-ias-platform-terraform-state-1234"
        key = "dev/terraform.tfstate"
        region = "ap-northeast-1"
        dynamodb_table = "terraform-lock-table"
        encrypt = true
        profile="cc-platform"
    }
}