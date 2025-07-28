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
                    // --- FIX for fatal: detected dubious ownership ---
                    // This dynamically adds the current workspace directory to Git's safe.directory
                    // configuration for the 'root' user inside the Docker container.
                    sh '''
                        CURRENT_WORKSPACE=$(pwd)
                        git config --global --add safe.directory "$CURRENT_WORKSPACE"
                        echo "Added $CURRENT_WORKSPACE to Git's safe directories for root user inside container."
                        git config --list --global # Verify the config was added
                    '''
                    // --- END FIX ---

                    env.BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()

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
