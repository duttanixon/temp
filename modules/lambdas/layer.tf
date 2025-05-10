# Define the layer requirements
resource "local_file" "layer_requirements" {
  content = <<-EOT
sqlalchemy>=2.0.0
pg8000==1.30.3
  EOT
  filename = "${path.module}/build/layer_requirements.txt"
  depends_on = [null_resource.create_build_dir]
}

# Create a shell script to build the layer
resource "local_file" "build_layer_script" {
  content = <<-EOT
#!/bin/bash
set -e

# Directory for layer building
LAYER_DIR=${path.module}/build/layer
mkdir -p $LAYER_DIR/python

# Install dependencies
pip3 install -r ${path.module}/build/layer_requirements.txt -t $LAYER_DIR/python

# Create layer zip
cd $LAYER_DIR
zip -r ../${var.environment}-city-eye-layer.zip .
  EOT
  filename = "${path.module}/build/build_layer.sh"
  depends_on = [local_file.layer_requirements]
}


# Make the script executable
resource "null_resource" "make_script_executable" {
  provisioner "local-exec" {
    command = "chmod +x ${path.module}/build/build_layer.sh"
  }
  depends_on = [local_file.build_layer_script]
}

# Build the layer
resource "null_resource" "build_layer" {
  provisioner "local-exec" {
    command = "${path.module}/build/build_layer.sh"
  }
  
  # Only rebuild if requirements change
  triggers = {
    requirements = local_file.layer_requirements.content
    script = local_file.build_layer_script.content
  }
  
  depends_on = [null_resource.make_script_executable]
}


# Lambda layer for SQLAlchemy and other dependencies
resource "aws_lambda_layer_version" "city_eye_dependencies" {
  layer_name = "${var.environment}-city-eye-dependencies"
  
  # We need to reference the layer zip file that was created by the build_layer script
  filename   = "${path.module}/build/${var.environment}-city-eye-layer.zip"
  
  compatible_runtimes = ["python3.9"]
  description = "Layer containing SQLAlchemy and PostgreSQL libraries for City Eye Lambda"
  
  depends_on = [null_resource.build_layer]
}