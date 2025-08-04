pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0' # Replace with a suitable image or executor
            args '-u root'
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
    }

    stages {
        
        stage('Install Dependencies') {
            steps {
                sh '''
                apt update
                apt install -y curl jq git
                '''
            }
        }

        stage('Download cortexcli') {
            steps {
                script {
                    def response = sh(script: """
                        curl --location '${env.CORTEX_API_URL}/public_api/v1/unified-cli/releases/download-link?os=linux&architecture=amd64' \
                          --header 'Authorization: ${env.CORTEX_API_KEY}' \
                          --header 'x-xdr-auth-id: ${env.CORTEX_API_KEY_ID}' \
                          --silent
                    """, returnStdout: true).trim()

                    def downloadUrl = sh(script: """echo '${response}' | jq -r '.signed_url'""", returnStdout: true).trim()

                    sh """
                        curl -o cortexcli '${downloadUrl}'
                        chmod +x cortexcli
                        ./cortexcli --version
                    """
                }
            }
        }

        stage('Run Scan') {
        // Replace the repo-id with your repository like: owner/repo
            steps {
                script {
                    unstash 'source'
                    def branchName = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()

                    sh """
                    ./cortexcli \
                      --api-base-url "${env.CORTEX_API_URL}" \
                      --api-key "${env.CORTEX_API_KEY}" \
                      --api-key-id "${env.CORTEX_API_KEY_ID}" \
                      code scan \
                      --directory "\$(pwd)" \
                      --repo-id <REPLACE WITH REPO_OWNER/REPO_NAME> \
                      --branch "${branchName}" \
                      --source "JENKINS" \
                      --create-repo-if-missing
                    """
                }
            }
        }
    }
}
