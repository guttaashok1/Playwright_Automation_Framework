#!/usr/bin/env groovy
/**
 * jenkins/vars/publishResults.groovy
 * Shared Library step — publishes test results to ADO, Confluence, Slack, Teams.
 *
 * Args (Map):
 *   pythonBin        : python executable   (default: 'python3')
 *   sprintName       : Confluence sprint   (default: '')
 *   notifySlack      : bool               (default: true)
 *   notifyTeams      : bool               (default: false)
 *   adoPublish       : bool               (default: true)
 *   confluencePublish: bool               (default: true)
 *   environment      : target env         (default: 'staging')
 */
def call(Map args = [:]) {

    args = [
        pythonBin        : 'python3',
        sprintName       : '',
        notifySlack      : true,
        notifyTeams      : false,
        adoPublish       : true,
        confluencePublish: true,
        environment      : 'staging',
    ] + args

    def suiteName   = "Jenkins Build #${env.BUILD_NUMBER} — ${args.environment.toUpperCase()}"
    def sprintArg   = args.sprintName ? "sprint_name='${args.sprintName}'," : ""
    def slackArg    = args.notifySlack  ? "True" : "False"
    def teamsArg    = args.notifyTeams  ? "True" : "False"

    sh """
        ${args.pythonBin} - <<'PYEOF'
import sys, os
sys.path.insert(0, '.')

from utils.reporter import TestReporter, TestResult
import json, glob

reporter = TestReporter()

# Load all results.json files written by the test run
for path in glob.glob('reports/**/results.json', recursive=True):
    with open(path) as f:
        data = json.load(f)
    for r in data.get('results', []):
        reporter.add_result(TestResult(
            name        = r['name'],
            status      = r['status'],
            duration_ms = r.get('duration_ms', 0),
            error       = r.get('error', ''),
        ))

reporter.publish(
    suite_name    = '${suiteName}',
    ${sprintArg}
    slack_notify  = ${slackArg},
    teams_notify  = ${teamsArg},
)
PYEOF
    """
}
