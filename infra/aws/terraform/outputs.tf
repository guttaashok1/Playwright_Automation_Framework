################################################################################
# outputs.tf — Useful values printed after `terraform apply`
################################################################################

output "jenkins_url" {
  description = "Jenkins Web UI URL"
  value       = "http://${aws_eip.jenkins.public_ip}:8080"
}

output "jenkins_admin_user" {
  description = "Jenkins admin username"
  value       = var.jenkins_admin_user
}

output "jenkins_admin_password_ssm" {
  description = "Retrieve the Jenkins password from SSM: aws ssm get-parameter --with-decryption --name <this>"
  value       = aws_ssm_parameter.jenkins_password.name
}

output "ec2_public_ip" {
  description = "Elastic IP attached to the Jenkins EC2 instance"
  value       = aws_eip.jenkins.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID (use for SSM Session Manager)"
  value       = aws_instance.jenkins.id
}

output "ssh_command" {
  description = "SSH command to connect (requires key_pair_name to be set)"
  value       = var.key_pair_name != "" ? "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.jenkins.public_ip}" : "No key pair configured — use SSM Session Manager instead"
}

output "ssm_session_command" {
  description = "Passwordless shell via AWS SSM Session Manager (no key pair needed)"
  value       = "aws ssm start-session --target ${aws_instance.jenkins.id} --region ${var.aws_region}"
}

output "retrieve_password_command" {
  description = "Command to fetch the Jenkins admin password from SSM"
  value       = "aws ssm get-parameter --name ${aws_ssm_parameter.jenkins_password.name} --with-decryption --query Parameter.Value --output text --region ${var.aws_region}"
}

output "free_tier_info" {
  description = "Free tier resource summary"
  value       = <<-EOT

  📋 FREE TIER USAGE (resets monthly):
    ✅ EC2 t2.micro  : 750 hrs/month — this instance uses ~744 hrs if always on
    ✅ EBS 30 GB     : 30 GB/month free — using full allocation
    ✅ Elastic IP    : Free while instance is RUNNING
    ⚠️  Elastic IP   : ~$3.65/month if instance is STOPPED
    ⚠️  Data transfer: 1 GB free outbound, then $0.09/GB

  💡 TIP: Stop the instance when not in use to preserve free hours:
    aws ec2 stop-instances --instance-ids ${aws_instance.jenkins.id} --region ${var.aws_region}
    aws ec2 start-instances --instance-ids ${aws_instance.jenkins.id} --region ${var.aws_region}
  EOT
}

output "setup_complete_message" {
  description = "Next steps"
  value       = <<-EOT

  ╔══════════════════════════════════════════════════════════════╗
  ║     🎉  Jenkins is being provisioned! (FREE TIER)            ║
  ║                                                              ║
  ║  Jenkins URL : http://${aws_eip.jenkins.public_ip}:8080         ║
  ║  Instance    : t2.micro  (1 vCPU / 1 GB RAM + 2 GB swap)    ║
  ║  Username    : ${var.jenkins_admin_user}                                ║
  ║  Password    : (see retrieve_password_command output)        ║
  ║                                                              ║
  ║  ⏳  First boot takes ~5-8 min on t2.micro (Docker pull).   ║
  ║  📋  Check startup logs via SSH:                             ║
  ║      ssh -i ~/.ssh/<key>.pem ubuntu@${aws_eip.jenkins.public_ip}  ║
  ║      sudo tail -f /var/log/jenkins-init.log                  ║
  ║                                                              ║
  ║  🔼  Upgrade tip: change instance_type to t3.medium          ║
  ║      after 12-month free tier expires for 4x more RAM.       ║
  ╚══════════════════════════════════════════════════════════════╝
  EOT
}
