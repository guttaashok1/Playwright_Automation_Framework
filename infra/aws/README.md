# Jenkins on AWS — Deployment Guide

> Deploys a Jenkins controller on **EC2 (t3.medium)** in **us-west-2** behind an Elastic IP,
> running inside Docker via Docker Compose with Jenkins Configuration-as-Code (JCasC).

---

## Architecture

```
Internet
   │
   ▼
Elastic IP (static)
   │
AWS VPC (10.0.0.0/16)
   └── Public Subnet (10.0.1.0/24)
          └── EC2 t3.medium (Ubuntu 22.04)
                 ├── Docker
                 │     ├── jenkins:lts-jdk17  → :8080 (Web UI)
                 │     │                      → :50000 (Agent JNLP)
                 │     └── docker:dind        → Docker-in-Docker builds
                 ├── IAM Role → SSM, CloudWatch
                 └── SSM Parameter Store → jenkins admin password
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| AWS CLI | ≥ 2.x | https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html |
| Terraform | ≥ 1.6 | https://developer.hashicorp.com/terraform/install |
| AWS Account | — | Configured with IAM user that has EC2/VPC/IAM/SSM permissions |

---

## Step 1 — Configure AWS credentials

```bash
aws configure
# AWS Access Key ID     : <your-access-key>
# AWS Secret Access Key : <your-secret-key>
# Default region name   : us-west-2
# Default output format : json
```

Verify:
```bash
aws sts get-caller-identity
```

---

## Step 2 — Create an EC2 Key Pair (for SSH access)

```bash
aws ec2 create-key-pair \
  --key-name playwright-jenkins-key \
  --region us-west-2 \
  --query "KeyMaterial" \
  --output text > ~/.ssh/playwright-jenkins-key.pem

chmod 400 ~/.ssh/playwright-jenkins-key.pem
```

---

## Step 3 — Restrict access to YOUR IP (recommended)

Find your public IP:
```bash
curl -s https://checkip.amazonaws.com
```

Edit `terraform/variables.tf` and set:
```hcl
variable "allowed_cidr_blocks" {
  default = ["YOUR.IP.ADDRESS.HERE/32"]
}
```

---

## Step 4 — Set your Jenkins admin password

Option A — Edit `variables.tf`:
```hcl
variable "jenkins_admin_password" {
  default = "MySecurePassword@2025!"
}
```

Option B — Use a `terraform.tfvars` file (recommended, gitignored):
```hcl
# terraform/terraform.tfvars
jenkins_admin_password = "MySecurePassword@2025!"
key_pair_name          = "playwright-jenkins-key"
```

---

## Step 5 — Deploy with Terraform

```bash
cd infra/aws/terraform

# Initialise providers
terraform init

# Preview what will be created
terraform plan

# Deploy (~2 minutes for resources, ~5 minutes for Jenkins to boot)
terraform apply
```

Terraform will print the outputs when done:
```
jenkins_url          = "http://1.2.3.4:8080"
ssh_command          = "ssh -i ~/.ssh/playwright-jenkins-key.pem ubuntu@1.2.3.4"
retrieve_password_command = "aws ssm get-parameter ..."
```

---

## Step 6 — Wait for Jenkins to start

Jenkins takes ~3–5 minutes after `terraform apply` to pull Docker images and start.

Monitor startup:
```bash
# SSH into the instance
ssh -i ~/.ssh/playwright-jenkins-key.pem ubuntu@<EC2_IP>

# Watch bootstrap log
sudo tail -f /var/log/jenkins-init.log

# Watch Docker Compose logs
sudo docker compose -f /opt/jenkins/docker-compose.yml logs -f
```

Or use SSM Session Manager (no key pair needed):
```bash
aws ssm start-session --target <INSTANCE_ID> --region us-west-2
```

---

## Step 7 — Log into Jenkins

1. Open `http://<EC2_IP>:8080` in your browser
2. Username: `admin`
3. Password: retrieve it with:
   ```bash
   aws ssm get-parameter \
     --name "/playwright-jenkins/jenkins_admin_password" \
     --with-decryption \
     --query "Parameter.Value" \
     --output text \
     --region us-west-2
   ```

---

## Step 8 — Connect Jenkins to your Git repository

1. **Jenkins → Manage Jenkins → Credentials → Global → Add Credentials**
   - Kind: `Secret text`
   - ID: `github-token`
   - Secret: Your GitHub PAT (with `repo` scope)

2. **Jenkins → New Item → Pipeline**
   - Name: `playwright-automation`
   - Pipeline → Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/your-org/your-repo.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

3. **Click Save → Build Now**

---

## Step 9 — Register the Shared Library

**Jenkins → Manage Jenkins → Configure System → Global Pipeline Libraries**

| Field | Value |
|---|---|
| Name | `playwright-shared-lib` |
| Default version | `main` |
| Retrieval method | Modern SCM |
| Git repo URL | `https://github.com/your-org/your-repo.git` |
| Library path | `jenkins` |

---

## Adding the `.env` Secrets to Jenkins

Your tests need the `.env` values (webhooks, ADO PAT, etc.).

```bash
# Upload your .env as a Jenkins Secret File credential
# Jenkins → Manage Jenkins → Credentials → Global → Add Credentials
#   Kind: Secret file
#   ID:   playwright-env-secrets
#   File: (upload your .env file)
```

The `Jenkinsfile` references it as:
```groovy
PLAYWRIGHT_SECRETS = credentials('playwright-env-secrets')
```

---

## Stopping / Destroying

```bash
# Tear down ALL AWS resources (stops billing)
cd infra/aws/terraform
terraform destroy
```

> ⚠️ This deletes the EC2 instance, EIP, VPC, and SSM parameters.
> Jenkins home data is lost unless you snapshot the EBS volume first.

---

## Cost Estimate (us-west-2)

### ✅ Free Tier (first 12 months)

| Resource | Free Tier Allowance | Usage |
|---|---|---|
| EC2 t2.micro | 750 hrs/month | ~744 hrs if always-on ✅ |
| EBS gp3 30 GB | 30 GB/month | Fully covered ✅ |
| Elastic IP (running) | Free | ✅ |
| Elastic IP (stopped) | $0.005/hr | ⚠️ ~$3.65/mo if stopped |
| SSM Standard params | Free | ✅ |
| Data outbound | 1 GB free | ✅ for light use |
| **Total** | | **$0/mo** (if instance stays running) |

### After Free Tier Expires

| Resource | Monthly Cost |
|---|---|
| EC2 t2.micro | ~$8.50/mo |
| EC2 t3.medium (upgrade) | ~$30/mo |
| EBS 30 GB gp3 | ~$2.40/mo |
| Elastic IP (in-use) | Free |
| **Total (t2.micro)** | **~$11/mo** |

> 💡 **Stop the instance when not running tests** to preserve free hours:
> ```bash
> # Stop (saves hours, EIP costs ~$0.005/hr while stopped)
> aws ec2 stop-instances --instance-ids <INSTANCE_ID> --region us-west-2
>
> # Start again
> aws ec2 start-instances --instance-ids <INSTANCE_ID> --region us-west-2
> ```

### Upgrading After Free Tier

Edit `terraform/variables.tf`:
```hcl
variable "instance_type" {
  default = "t3.medium"   # 2 vCPU / 4 GB RAM
}
```

Then in `docker-compose.yml`:
- Remove `mem_limit` and `memswap_limit`
- Change `-Xmx512m` → `-Xmx2g`
- Uncomment the `dind` service
- Change `numExecutors: 1` → `2` in JCasC
