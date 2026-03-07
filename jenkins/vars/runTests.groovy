#!/usr/bin/env groovy
/**
 * jenkins/vars/runTests.groovy
 * Shared Library step — executes pytest for a given suite and browser list.
 *
 * Args (Map):
 *   suite      : 'api' | 'ui'
 *   markers    : pytest -m expression  (e.g. "ui and smoke")
 *   browsers   : list of browser names (default: ['chromium'])
 *   pythonBin  : python executable     (default: 'python3')
 *   environment: target env            (default: 'staging')
 *   testSuite  : suite tag             (default: 'smoke')
 */
def call(Map args = [:]) {

    args = [
        suite      : 'ui',
        markers    : 'smoke',
        browsers   : ['chromium'],
        pythonBin  : 'python3',
        environment: 'staging',
        testSuite  : 'smoke',
    ] + args

    def browserFlags = args.browsers.collect { "--browser=${it}" }.join(' ')
    def testDir      = "tests/${args.suite}/"
    def reportSuffix = "${args.suite}-${args.environment}"

    sh """
        ${args.pythonBin} -m pytest ${testDir} \\
            -m "${args.markers}" \\
            ${browserFlags} \\
            -n auto \\
            --dist=loadfile \\
            --reruns=2 \\
            --reruns-delay=1 \\
            --alluredir=reports/allure-results \\
            --html=reports/report-${reportSuffix}.html \\
            --self-contained-html \\
            --screenshot=only-on-failure \\
            --video=retain-on-failure \\
            --tracing=retain-on-failure \\
            --output=reports/artifacts/${reportSuffix} \\
            -v \\
            --tb=short \\
            --override-ini="addopts=" \\
            -q
    """
}
