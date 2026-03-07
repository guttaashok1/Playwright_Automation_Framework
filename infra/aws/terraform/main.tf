################################################################################
# main.tf — Playwright Jenkins on AWS EC2 + Docker  (us-west-2)
#
# Resources created:
#   VPC → Internet Gateway → Public Subnet → Route Table
#   Security Group (SSH + 8080 + 50000)
#   IAM Role + Instance Profile  (SSM access + CloudWatch logs)
#   EC2 Instance (Ubuntu 22.04, Docker, Jenkins via docker-compose)
#   Elastic IP  (static address)
#   SSM Parameter (Jenkins admin password)
################################################################################

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: uncomment to store state in S3
  # backend "s3" {
  #   bucket = "your-tf-state-bucket"
  #   key    = "playwright-jenkins/terraform.tfstate"
  #   region = "us-west-2"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ── AMI: latest Ubuntu 22.04 LTS (Jammy) ─────────────────────────────────────
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

################################################################################
# Networking
################################################################################

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = { Name = "${var.project_name}-public-subnet" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

################################################################################
# Security Group
################################################################################

resource "aws_security_group" "jenkins" {
  name        = "${var.project_name}-sg"
  description = "Jenkins controller: SSH, UI, agent JNLP"
  vpc_id      = aws_vpc.main.id

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # Jenkins Web UI
  ingress {
    description = "Jenkins UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # Jenkins agent JNLP
  ingress {
    description = "Jenkins Agent JNLP"
    from_port   = 50000
    to_port     = 50000
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg" }
}

################################################################################
# IAM — EC2 instance role
################################################################################

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "jenkins" {
  name               = "${var.project_name}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

# SSM Session Manager (zero-trust SSH alternative)
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.jenkins.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# CloudWatch agent logs
resource "aws_iam_role_policy_attachment" "cloudwatch" {
  role       = aws_iam_role.jenkins.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Read SSM parameters (for Jenkins secrets)
resource "aws_iam_role_policy" "ssm_params" {
  name = "ssm-parameter-read"
  role = aws_iam_role.jenkins.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
      ]
      Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/*"
    }]
  })
}

resource "aws_iam_instance_profile" "jenkins" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.jenkins.name
}

################################################################################
# SSM Parameter — Jenkins admin password (encrypted)
################################################################################

resource "aws_ssm_parameter" "jenkins_password" {
  name        = "/${var.project_name}/jenkins_admin_password"
  description = "Jenkins admin password"
  type        = "SecureString"
  value       = var.jenkins_admin_password

  tags = { Name = "${var.project_name}-jenkins-password" }
}

################################################################################
# EC2 Instance
################################################################################

resource "aws_instance" "jenkins" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.jenkins.id]
  iam_instance_profile   = aws_iam_instance_profile.jenkins.name
  key_name               = var.key_pair_name != "" ? var.key_pair_name : null

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    delete_on_termination = true
    encrypted             = true

    tags = { Name = "${var.project_name}-root-ebs" }
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    project_name           = var.project_name
    jenkins_version        = var.jenkins_version
    jenkins_admin_user     = var.jenkins_admin_user
    aws_region             = var.aws_region
    ssm_password_param     = aws_ssm_parameter.jenkins_password.name
  })

  user_data_replace_on_change = true

  tags = { Name = "${var.project_name}-controller" }

  # Ensure SSM parameter is created first (user_data reads it at boot)
  depends_on = [aws_ssm_parameter.jenkins_password]
}

################################################################################
# Elastic IP — keeps the Jenkins URL stable across stop/start
################################################################################

resource "aws_eip" "jenkins" {
  instance = aws_instance.jenkins.id
  domain   = "vpc"

  tags = { Name = "${var.project_name}-eip" }

  depends_on = [aws_internet_gateway.main]
}
