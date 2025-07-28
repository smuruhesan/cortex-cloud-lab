pipeline {
    agent {
        docker {
            image 'jenkins/agent:alpine'
            args '-u root --privileged -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
        CORTEX_CLI_VERSION = '0.13.0'
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                // This 'checkout scm' step is usually handled by Jenkins' SCM polling
                // and might not be the direct cause of the dubious ownership if it's
                // the 'git rev-parse' later that fails.
                checkout scm
                stash includes: '**/*', name: 'source'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                apk add --no-cache jq docker
                '''
            }
        }

        stage('Get Temporary Token') {
            environment {
                TEMP_TOKEN = ""
            }
            steps {
                script {
                    def response = sh(script: """
                        curl --location '${env.CORTEX_API_URL}/public_api/v1/unified-cli/image/token' \\
                          --header 'Authorization: ${env.CORTEX_API_KEY}' \\
                          --header 'x-xdr-auth-id: ${env.CORTEX_API_KEY_ID}' \\
                          --header 'Content-Type: application/json' \\
                          --data '{}' \\
                          -s
                    """, returnStdout: true).trim()

                    env.TEMP_TOKEN = sh(script: """echo '${response}' | jq -r '.token'""", returnStdout: true).trim()
                }
            }
        }

        stage('Pull Docker Image') {
            steps {
                sh """
                docker pull distributions.traps.paloaltonetworks.com/cli-docker/${env.TEMP_TOKEN}/method:amd64-${env.CORTEX_CLI_VERSION}
                docker tag distributions.traps.paloaltonetworks.com/cli-docker/${env.TEMP_TOKEN}/method:amd64-${env.CORTEX_CLI_VERSION} cortexcli:${env.CORTEX_CLI_VERSION}
                """
            }
        }

        stage('Run Docker Container (Code Scan)') {
            steps {
                script {
                    unstash 'source'
 // --- BEGIN Recommended Config for Dubious Ownership ---
                        sh '''
                            echo '#!/bin/sh' > /tmp/git-askpass.sh
                            echo 'exit 0' >> /tmp/git-askpass.sh
                            chmod +x /tmp/git-askpass.sh
                        '''
                        // Wrap the git command in a withEnv block to set GIT_ASKPASS
                        withEnv(["GIT_ASKPASS=/tmp/git-askpass.sh"]) {
                            // --- BEGIN DEBUGGING COMMANDS ---
                            sh 'echo "Current user: $(whoami)"'
                            sh 'echo "Current user ID and groups: $(id)"'
                            sh 'echo "GIT_ASKPASS variable: $GIT_ASKPASS"'
                            sh 'echo "Permissions of git-askpass.sh:"'
                            sh 'ls -l /tmp/git-askpass.sh'
                            sh 'echo "Contents of git-askpass.sh:"'
                            sh 'cat /tmp/git-askpass.sh'
                            sh 'echo "Git global config:"'
                            sh 'git config --list --global'
                            sh 'echo "Git local config (if any):"'
                            sh 'git config --list --local || true' # '|| true' to prevent failure if no local config
                            sh 'echo "Ownership of workspace directory:"'
                            sh 'ls -ld /var/lib/jenkins/workspace/Cortex-Cloud-Scan-Test*' // Adjust if your job name is different
                            // --- END DEBUGGING COMMANDS ---

                        env.BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()
                    }
                    // --- END Recommended Config for Dubious Ownership ---

                    sh """
                    docker run --rm -v \$(pwd):/home/code cortexcli:${env.CORTEX_CLI_VERSION} \\
                      --api-base-url ${env.CORTEX_API_URL} \\
                      --api-key ${env.CORTEX_API_KEY} \\
                      --api-key-id ${env.CORTEX_API_KEY_ID} \\
                      code scan \\
                      --directory /home/code \\
                      --repo-id smuruhesan/cortex-cloud-lab \\ // Your GitHub repo owner/name
                      --branch ${env.BRANCH} \\
                      --source JENKINS \\
                      --create-repo-if-missing
                    """
                }
            }
        }
    }
}
