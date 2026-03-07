#!/usr/bin/env groovy
/**
 * Playwright Automation — Root Jenkinsfile
 *
 * Uses the 'playwright-shared-lib' Jenkins Shared Library defined in jenkins/vars/.
 * Configure the library in Jenkins → Manage Jenkins → Configure System → Global Pipeline Libraries:
 *   Name            : playwright-shared-lib
 *   Default version : main
 *   Source          : (this same Git repository, path: jenkins)
 */
@Library('playwright-shared-lib') _

playwrightPipeline(
    environment      : params.ENVIRONMENT  ?: 'staging',
    testSuite        : params.TEST_SUITE   ?: 'smoke',
    browsers         : (params.BROWSER == 'all')
                           ? ['chromium', 'firefox', 'webkit']
                           : [params.BROWSER ?: 'chromium'],
    sprintName       : params.SPRINT_NAME  ?: '',
    notifySlack      : true,
    notifyTeams      : true,
    adoPublish       : true,
    confluencePublish: true,
)
