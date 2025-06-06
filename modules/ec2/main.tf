# EBS volume storage
resource "aws_ebs_volume" "app_data" {
    availability_zone       = "${var.aws_region}${var.availability_zone}"
    size                = var.data_volume_size
    type                =   "gp3"

    tags = {
        Name = "${var.environment}-app-data"
    }
}
# Generate a new SSH key pair
resource "tls_private_key" "ec2_app_server_key" {
    algorithm   = "RSA"
    rsa_bits    = 4096
}

# Create directory for keys if it doesn't exist
resource "null_resource" "create_keys_dir" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/keys"
  }
}

# Save the private key to the local file
resource "local_file" "private_key" {
    content             = tls_private_key.ec2_app_server_key.private_key_pem
    filename            = "${path.module}/keys/${var.environment}-app-server-key.pem"
    file_permission     = "0600"
}

# Key pair for SSH access upload to AWS
resource "aws_key_pair" "app_server_key" {
    key_name    = "${var.environment}-ec2-app-server-key"
    public_key  = tls_private_key.ec2_app_server_key.public_key_openssh
}

# EC2 Spot Instance
resource "aws_instance" "app_server" {
    ami                     = "ami-026c39f4021df9abe"
    instance_type           = var.instance_type
    key_name                = aws_key_pair.app_server_key.key_name
    vpc_security_group_ids  = [aws_security_group.app_server_sg.id]
    iam_instance_profile    = aws_iam_instance_profile.ec2_profile.name
    availability_zone       = "${var.aws_region}${var.availability_zone}"

    root_block_device {
        volume_size = 20
        volume_type = "gp3"
        encrypted   = true
    }

    user_data = templatefile("${path.module}/scripts/user_data.sh", {

        app_volume_id       = aws_ebs_volume.app_data.id
        s3_backup_bucket    = aws_s3_bucket.app_backups.bucket
        environment         = var.environment
        region              = var.aws_region
        engineer_keys       = var.engineer_ssh_keys
    })

    tags = {
        Name = "${var.environment}-ec2-app-server"
    }

    depends_on = [
        aws_ebs_volume.app_data,
        aws_s3_bucket.app_backups
    ]
}

# Volumne attachment for spot instance

resource "aws_volume_attachment" "app_attachment" {
    device_name     = "/dev/sdf"
    volume_id       = aws_ebs_volume.app_data.id
    instance_id     = aws_instance.app_server.id

    # Prevent terraform from destroying the volume when it's detached
    skip_destroy = true
}

resource "aws_eip" "app_server_eip" {
    domain = "vpc"

    tags = {
        Name = "${var.environment}-app-server-eip"
    }
}

resource "aws_eip_association" "app_server_eip_assoc" {
    instance_id     = aws_instance.app_server.id
    allocation_id   = aws_eip.app_server_eip.id
}