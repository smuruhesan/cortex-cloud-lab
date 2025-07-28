pipeline {
    agent {
        docker {
            image 'jenkins/agent:alpine'
            args '-u root --privileged -v /var/run/docker.sock:/var/run/docker.sock'
            // IMPORTANT: Replace this with the actual label of your Jenkins agent that has Docker installed
            label 'Sarav-Jenkins' // <-- **REPLACE THIS** with your agent's label (e.g., 'my-docker-node')
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
        CORTEX_CLI_VERSION = '0.13.0'
    }

// Added Extra starts - to checkout Source Code
    stages {
        stage('Checkout Source Code') {
            steps {
                // Checkout your Git repository
                // Make sure your Jenkins job is configured to use SCM (Git)
                // When using a Pipeline job with SCM, Jenkins automatically checks out the code.
                // We'll stash it for later use by the docker run command.
                checkout scm
                stash includes: '**/*', name: 'source' // Stash all files for later use by the Docker container
            }
        }

// Added Extra ends

        stage('Install Dependencies') {
            steps {
                sh '''
                apk add --no-cache jq docker
                '''
            }
        }

        stage('Get Temporary Token') {
            environment {
                TEMP_TOKEN = "" // Initialize TEMP_TOKEN for this stage
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
        // Replace the repo-id with your repository like: owner/repo
            steps {
                script {
                    unstash 'source' // Retrieve the source code stashed in the "Checkout" stage
                    // Get current branch name (assuming a Git checkout has occurred)
                    env.BRANCH = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()

                    sh """
                    docker run --rm -v \$(pwd):/home/code cortexcli:${env.CORTEX_CLI_VERSION} \\
                      --api-base-url ${env.CORTEX_API_URL} \\
                      --api-key ${env.CORTEX_API_KEY} \\
                      --api-key-id ${env.CORTEX_API_KEY_ID} \\
                      code scan \\
                      --directory /home/code \\
                      --repo-id smuruhesan/cortex-cloud-lab \\ // <-- **REPLACE THIS** (e.g., myuser/my-sample-repo)
                      --branch ${env.BRANCH} \\
                      --source JENKINS \\
                      --create-repo-if-missing
                    """
                }
            }
        }
    }
}
