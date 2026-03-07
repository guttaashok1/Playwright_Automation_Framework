#!/usr/bin/env groovy
/**
 * jenkins/vars/playwrightPipeline.groovy
 * Shared Library — top-level pipeline definition.
 *
 * Usage from Jenkinsfile:
 *   playwrightPipeline(
 *       environment : 'staging',
 *       testSuite   : 'smoke',
 *       browsers    : ['chromium', 'firefox'],
 *       sprintName  : 'Sprint 42',
 *       notifySlack : true,
 *       notifyTeams : true,
 *       adoPublish  : true,
 *       confluencePublish: true,
 *   )
 */
def call(Map cfg = [:]) {

    // ── Defaults ───────────────────────────────────────────────────────────
    cfg = [
        environment      : 'staging',
        testSuite        : 'smoke',
        browsers         : ['chromium'],
        sprintName       : '',
        notifySlack      : true,
        notifyTeams      : false,
        adoPublish       : true,
        confluencePublish: true,
        pythonBin        : 'python3',
    ] + cfg

    pipeline {
        agent any

        // ── Build parameters (visible in Jenkins UI) ────────────────────────
        parameters {
            choice(
                name        : 'ENVIRONMENT',
                choices     : ['staging', 'dev', 'prod'],
                description : 'Target environment'
            )
            choice(
                name        : 'TEST_SUITE',
                choices     : ['smoke', 'regression', 'all'],
                description : 'Test suite to run'
            )
            choice(
                name        : 'BROWSER',
                choices     : ['chromium', 'firefox', 'webkit', 'all'],
                description : 'Browser(s) to use'
            )
            string(
                name        : 'SPRINT_NAME',
                defaultValue: '',
                description : 'Sprint name for Confluence doc (e.g. Sprint 42)'
            )
        }

        // ── Environment variables ────────────────────────────────────────────
        environment {
            PYTHON          = "${cfg.pythonBin}"
            ENVIRONMENT     = "${cfg.environment}"
            CI              = 'true'
            // Jenkins secret file — contains .env contents (PAT, webhooks, creds)
            PLAYWRIGHT_SECRETS = credentials('playwright-env-secrets')
        }

        // ── Options ─────────────────────────────────────────────────────────
        options {
            timeout(time: 60, unit: 'MINUTES')
            buildDiscarder(logRotator(numToKeepStr: '30'))
            disableConcurrentBuilds()
            ansiColor('xterm')
        }

        stages {

            // ── 1. Setup ─────────────────────────────────────────────────────
            stage('Setup') {
                steps {
                    script { runSetup(cfg) }
                }
            }

            // ── 2. Lint ──────────────────────────────────────────────────────
            stage('Lint') {
                steps {
                    script { runLint(cfg) }
                }
            }

            // ── 3. Tests (parallel API + UI) ─────────────────────────────────
            stage('Tests') {
                parallel {
                    stage('API Tests') {
                        steps {
                            script {
                                runTests(cfg + [suite: 'api', markers: 'api'])
                            }
                        }
                    }
                    stage('UI Tests') {
                        steps {
                            script {
                                runTests(cfg + [suite: 'ui', markers: "ui and ${cfg.testSuite}"])
                            }
                        }
                    }
                }
            }

            // ── 4. Publish results ────────────────────────────────────────────
            stage('Publish') {
                steps {
                    script { publishResults(cfg) }
                }
            }
        }

        // ── Post actions ─────────────────────────────────────────────────────
        post {
            always {
                // Archive all report artifacts
                archiveArtifacts(
                    artifacts      : 'reports/**',
                    allowEmptyArchive: true
                )
                // Publish Allure report (requires Allure Jenkins plugin)
                allure([
                    includeProperties  : false,
                    jdk                : '',
                    reportBuildPolicy  : 'ALWAYS',
                    results            : [[path: 'reports/allure-results']]
                ])
                // Publish pytest-html report (requires HTML Publisher plugin)
                publishHTML([
                    allowMissing         : true,
                    alwaysLinkToLastBuild: true,
                    keepAll              : true,
                    reportDir            : 'reports',
                    reportFiles          : 'report.html',
                    reportName           : 'Playwright Test Report'
                ])
            }
            failure {
                script {
                    echo "[Pipeline] Build FAILED — sending notifications"
                    if (cfg.notifySlack) {
                        sh """${env.PYTHON} -c "
from utils.reporter import TestReporter
r = TestReporter()
r._notify_slack_raw(
    text=':x: *Build #${env.BUILD_NUMBER} FAILED* — ${cfg.environment.toUpperCase()}\\n'
         + '> <${env.BUILD_URL}|View build>'
)
" """
                    }
                }
            }
            success {
                echo "[Pipeline] Build SUCCEEDED"
            }
            cleanup {
                cleanWs()
            }
        }
    }
}

// ── Helper steps (inlined for single-file simplicity) ─────────────────────────

def runSetup(Map cfg) {
    sh """
        # Copy injected secrets to .env
        cp \${PLAYWRIGHT_SECRETS} .env

        # Install Python dependencies
        ${cfg.pythonBin} -m pip install --quiet --upgrade pip
        ${cfg.pythonBin} -m pip install --quiet -r requirements.txt

        # Install Playwright browsers
        ${cfg.pythonBin} -m playwright install --with-deps chromium firefox webkit

        # Ensure report directories exist
        mkdir -p reports/allure-results reports/artifacts reports/visual_diffs
    """
}

def runLint(Map cfg) {
    sh """
        ${cfg.pythonBin} -m flake8 . \
            --max-line-length=120 \
            --exclude=.git,__pycache__,.venv,reports \
            --count --statistics || true
    """
}
