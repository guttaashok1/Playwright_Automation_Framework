################################################################################
# variables.tf — Playwright Jenkins on AWS (us-west-2)
#
# ⚠️  FREE TIER LIMITS (12 months from account creation):
#   • EC2 : 750 hrs/month of t2.micro  (Linux)
#   • EBS : 30 GB gp2/gp3 storage
#   • EIP : Free while instance is RUNNING; $0.005/hr if instance is stopped
#   • SSM : Standard parameters are free
#   • Data: 1 GB outbound free, then $0.09/GB
#
# t2.micro = 1 vCPU / 1 GB RAM → Jenkins needs a swap file to stay stable.
################################################################################

variable "aws_region" {
  description = "AWS region to deploy Jenkins into"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Used to prefix all resource names"
  type        = string
  default     = "playwright-jenkins"
}

variable "environment" {
  description = "Environment tag (dev | staging | prod)"
  type        = string
  default     = "dev"
}

# ── Networking ────────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for the new VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "AZ for the public subnet (must be in aws_region)"
  type        = string
  default     = "us-west-2a"
}

variable "allowed_cidr_blocks" {
  description = <<-EOT
    List of CIDRs allowed to reach Jenkins port 8080 and SSH port 22.
    Restrict to YOUR IP for security: ["x.x.x.x/32"]
    Default allows all (0.0.0.0/0) — fine for a quick PoC, NOT for production.
  EOT
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ── EC2 ───────────────────────────────────────────────────────────────────────

variable "instance_type" {
  description = <<-EOT
    EC2 instance type for the Jenkins controller.
    FREE TIER: t2.micro (1 vCPU / 1 GB RAM) — bootstrap adds 2 GB swap to compensate.
    Upgrade to t3.medium (2 vCPU / 4 GB) after free tier expires for better performance.
  EOT
  type        = string
  default     = "t2.micro"   # ✅ Free Tier eligible (750 hrs/month)
}

variable "key_pair_name" {
  description = <<-EOT
    Name of an EXISTING AWS key pair for SSH access.
    Create one in EC2 → Key Pairs and download the .pem file first.
    Leave empty to skip SSH key attachment.
  EOT
  type        = string
  default     = ""
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GiB (Jenkins home + Docker images)"
  type        = number
  default     = 30
}

# ── Jenkins ───────────────────────────────────────────────────────────────────

variable "jenkins_version" {
  description = "Jenkins Docker image tag"
  type        = string
  default     = "lts-jdk17"
}

variable "jenkins_admin_user" {
  description = "Initial Jenkins admin username"
  type        = string
  default     = "admin"
}

variable "jenkins_admin_password" {
  description = <<-EOT
    Initial Jenkins admin password.
    CHANGE THIS before deploying! Also stored in SSM Parameter Store.
  EOT
  type        = string
  default     = "Jenkins@2025!"
  sensitive   = true
}
