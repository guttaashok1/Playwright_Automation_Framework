#!/usr/bin/env bash
# =============================================================================
# user_data.sh — EC2 bootstrap script (runs as root on first boot)
# Installs: Docker, Docker Compose, AWS CLI v2, Jenkins (via docker-compose)
#
# ⚠️  FREE TIER OPTIMISED (t2.micro: 1 vCPU / 1 GB RAM):
#   • Creates a 2 GB swap file to prevent OOM kills
#   • JVM heap capped at 512m (vs 2g for t3.medium)
#   • Docker-in-Docker removed (saves ~200 MB RAM)
#   • Minimal plugin set pre-installed
#
# Templated by Terraform — variables: ${project_name}, ${jenkins_version},
#   ${jenkins_admin_user}, ${aws_region}, ${ssm_password_param}
# =============================================================================
set -euo pipefail
exec > /var/log/jenkins-init.log 2>&1
echo "=== Bootstrap started at $(date) ==="

PROJECT_NAME="${project_name}"
JENKINS_VERSION="${jenkins_version}"
JENKINS_ADMIN_USER="${jenkins_admin_user}"
AWS_REGION="${aws_region}"
SSM_PASSWORD_PARAM="${ssm_password_param}"
JENKINS_HOME="/opt/jenkins/home"
COMPOSE_DIR="/opt/jenkins"

# ── 0. FREE TIER: Create 2 GB swap file (essential for 1 GB RAM) ─────────────
echo "--- Configuring swap (2 GB) ---"
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  # Reduce swap aggressiveness — only swap under memory pressure
  echo 'vm.swappiness=10'           >> /etc/sysctl.conf
  echo 'vm.vfs_cache_pressure=50'   >> /etc/sysctl.conf
  sysctl -p
fi
free -h   # Log current memory

# ── 1. System packages ────────────────────────────────────────────────────────
echo "--- Installing system packages ---"
apt-get update -qq
apt-get install -y -qq \
  curl wget unzip git jq \
  ca-certificates gnupg lsb-release \
  apt-transport-https software-properties-common

# ── 2. AWS CLI v2 ─────────────────────────────────────────────────────────────
echo "--- Installing AWS CLI v2 ---"
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp/
/tmp/aws/install --update
aws --version

# ── 3. Docker Engine ──────────────────────────────────────────────────────────
echo "--- Installing Docker ---"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -qq
apt-get install -y -qq \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable & start Docker
systemctl enable docker
systemctl start docker

# Limit Docker log sizes to preserve disk space (30 GB free tier EBS)
cat > /etc/docker/daemon.json <<DAEMON
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
DAEMON
systemctl restart docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

docker --version
docker compose version

# ── 4. Fetch Jenkins admin password from SSM ──────────────────────────────────
echo "--- Fetching Jenkins password from SSM ---"
JENKINS_ADMIN_PASSWORD=$(aws ssm get-parameter \
  --name "$SSM_PASSWORD_PARAM" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text \
  --region "$AWS_REGION" 2>/dev/null || echo "Jenkins@ChangeMe!")

# ── 5. Create Jenkins directories ─────────────────────────────────────────────
echo "--- Setting up Jenkins directories ---"
mkdir -p "$JENKINS_HOME" /opt/jenkins/casc
# Jenkins runs as UID 1000 inside the container
chown -R 1000:1000 "$JENKINS_HOME"

# ── 6. Jenkins Configuration-as-Code (JCasC) ──────────────────────────────────
echo "--- Writing JCasC config ---"
cat > /opt/jenkins/casc/jenkins.yaml <<CASC
jenkins:
  systemMessage: "🎭 Playwright Automation — Jenkins | t2.micro Free Tier | Managed by JCasC"
  # Free tier: keep executors low to avoid memory pressure
  numExecutors: 1
  mode: NORMAL
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: "$${JENKINS_ADMIN_USER}"
          password: "$${JENKINS_ADMIN_PASSWORD}"
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false

unclassified:
  location:
    url: "http://localhost:8080/"
    adminAddress: "admin@example.com"

  globalLibraries:
    libraries:
      - name: "playwright-shared-lib"
        defaultVersion: "main"
        retriever:
          modernSCM:
            scm:
              git:
                remote: "https://github.com/your-org/your-repo.git"
                credentialsId: "github-token"

tool:
  git:
    installations:
      - name: "Default"
        home: "git"
CASC

# ── 7. Docker Compose file (free-tier optimised) ─────────────────────────────
# NOTE: Docker-in-Docker removed — too heavy for 1 GB RAM.
# Tests run directly via pytest (not inside a nested Docker build).
echo "--- Writing docker-compose.yml ---"
cat > "$COMPOSE_DIR/docker-compose.yml" <<COMPOSE
version: "3.9"

services:
  jenkins:
    image: jenkins/jenkins:$${JENKINS_VERSION}
    container_name: jenkins
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - $${JENKINS_HOME}:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /opt/jenkins/casc:/var/jenkins_home/casc_configs:ro
    environment:
      CASC_JENKINS_CONFIG: /var/jenkins_home/casc_configs
      # ⚠️  Free tier: heap capped at 512m (not 2g)
      JAVA_OPTS: >-
        -Djenkins.install.runSetupWizard=false
        -Dhudson.model.DirectoryBrowserSupport.CSP=
        -Xms256m
        -Xmx512m
        -XX:+UseG1GC
        -XX:MaxGCPauseMillis=200
        -Djava.awt.headless=true
      JENKINS_OPTS: "--prefix=/"
    # Hard container memory limit — prevents OOM kill of host
    mem_limit: 700m
    memswap_limit: 1400m
    user: root
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8080/login || exit 1"]
      interval: 45s
      timeout: 15s
      retries: 10
      start_period: 180s   # Give more time on slow t2.micro first boot
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"

volumes:
  jenkins_home:
    driver: local
COMPOSE

# ── 8. Minimal plugin list (keep small for free tier disk) ───────────────────
echo "--- Writing plugins list ---"
cat > /opt/jenkins/plugins.txt <<PLUGINS
git:latest
workflow-aggregator:latest
pipeline-stage-view:latest
allure-jenkins-plugin:latest
html-publisher:latest
build-timeout:latest
timestamper:latest
ws-cleanup:latest
credentials-binding:latest
github:latest
github-branch-source:latest
PLUGINS

# ── 9. Pre-install plugins into Jenkins home ──────────────────────────────────
echo "--- Pre-installing Jenkins plugins (this may take a few minutes) ---"
docker pull jenkins/jenkins:$JENKINS_VERSION

docker run --rm \
  -v "$JENKINS_HOME:/var/jenkins_home" \
  --user root \
  --memory="600m" \
  jenkins/jenkins:$JENKINS_VERSION \
  jenkins-plugin-cli --plugin-file /dev/stdin <<< "$(cat /opt/jenkins/plugins.txt)" || true

# Fix ownership after docker run
chown -R 1000:1000 "$JENKINS_HOME"

# ── 10. systemd service ───────────────────────────────────────────────────────
echo "--- Creating systemd service ---"
cat > /etc/systemd/system/jenkins.service <<SERVICE
[Unit]
Description=Jenkins CI via Docker Compose (Free Tier)
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=forking
WorkingDirectory=/opt/jenkins
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose restart
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable jenkins.service

# ── 11. Start Jenkins ─────────────────────────────────────────────────────────
echo "--- Starting Jenkins ---"
cd "$COMPOSE_DIR"
docker compose up -d

PUBLIC_IP=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/public-ipv4 || echo "<ELASTIC_IP>")

echo ""
echo "=================================================================="
echo "=== Bootstrap finished at $(date)              ==="
echo "=== Jenkins starting (allow 3-5 min on t2.micro)              ==="
echo "=== UI → http://$PUBLIC_IP:8080                               ==="
echo "=== Logs → docker compose -f $COMPOSE_DIR/docker-compose.yml logs -f ==="
echo "=================================================================="
