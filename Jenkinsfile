pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0'
            args '-u root' // Keeping this as per your working Jenkinsfile
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
        AZURE_CREDENTIALS_ID = 'azure-service-principal'
    }

    stages {
        stage('Clean Workspace and Checkout Source Code') {
            steps {
                deleteDir()
                checkout scm
                stash includes: '**/*', name: 'source'
            }
        }

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
                        curl --location '${env.CORTEX_API_URL}/public_api/v1/unified-cli/releases/download-link?os=linux&architecture=amd64' --header 'Authorization: ${env.CORTEX_API_KEY}' --header 'x-xdr-auth-id: ${env.CORTEX_API_KEY_ID}' --silent
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
            steps {
                script {
                    unstash 'source'
                    sh 'echo "--- Run Scan Stage: After unstash ---"'
                    sh 'pwd'
                    sh 'ls -l'
                    sh 'ls -l terraform/'

                    sh """
                    ./cortexcli \\
                      --api-base-url "${env.CORTEX_API_URL}" \\
                      --api-key "${env.CORTEX_API_KEY}" \\
                      --api-key-id "${env.CORTEX_API_KEY_ID}" \\
                      code scan \\
                      --directory "terraform/" \\
                      --repo-id "smuruhesan/cortex-cloud-lab" \\
                      --branch "main" \\
                      --source "JENKINS" \\
                      --create-repo-if-missing
                    """
                }
            }
        }

        stage('Deploy Azure Infrastructure (Optional)') {
            steps {
                script {
                    unstash 'source'

                    sh 'echo "--- Deploy Stage: After unstash ---"'
                    sh 'pwd'
                    sh 'ls -l'
                    sh 'ls -l terraform/'

                    def repoId = "YOUR_GITHUB_USERNAME/cortex-cloud-lab"
                    def githubUsername = repoId.split('/')[0]

                    sh '''
                    if ! command -v terraform &> /dev/null
                    then
                        echo "Terraform not found, installing..."
                        apt update && apt install -y unzip
                        rm -f /usr/local/bin/terraform
                        rm -rf /usr/local/bin/terraform/
                        mkdir -p /usr/local/bin/
                        curl -o /usr/local/bin/terraform_1.7.5_linux_amd64.zip https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip
                        unzip -o /usr/local/bin/terraform_1.7.5_linux_amd64.zip -d /usr/local/bin/
                        rm /usr/local/bin/terraform_1.7.5_linux_amd64.zip
                        terraform --version
                    fi
                    '''

                    withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                        dir('terraform') {
                            sh 'rm -f .terraform.lock.hcl'

                            sh 'echo "--- Deploy Stage: Inside terraform/ dir before init ---"'
                            sh 'pwd'
                            sh 'ls -l .'

                            sh 'terraform init'
                            sh "terraform plan -out=tfplan -var='username=${githubUsername}'"
                            sh "terraform apply -auto-approve tfplan"
                            // REMOVE: rm -rf .terraform from here, it will be in post section
                        }
                    }
                }
            }
        }
    } // End of stages block

    // NEW: Post-build actions for cleanup
    post {
        always { // This block runs regardless of pipeline success or failure
            script {
                // Ensure the Docker container is still running and has access to the workspace
                // This sh command will execute inside the Docker agent container
                sh '''
                    echo "--- Post-build Cleanup: Removing .terraform directory ---"
                    # Navigate to the workspace root
                    cd /var/lib/jenkins/workspace/cortex-cloud-lab-pipeline/ # Adjust if your workspace path is different
                    
                    # Forcefully remove the .terraform directory
                    if [ -d "terraform/.terraform" ]; then
                        rm -rf terraform/.terraform
                        echo "Successfully removed terraform/.terraform"
                    else
                        echo "terraform/.terraform directory not found or already removed."
                    fi
                    
                    # Also clean up any remaining .terraform.lock.hcl at the root if it somehow ended up there
                    rm -f .terraform.lock.hcl
                '''
            }
        }
    }
}
