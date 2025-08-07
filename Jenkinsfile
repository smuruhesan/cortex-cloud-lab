pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0'
            // THIS IS THE CRUCIAL FIX. It bypasses the AppArmor permission issue.
            args '-u root --security-opt apparmor=unconfined'
        }
    }

    environment {
        CORTEX_API_KEY      = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID   = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL      = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
        AZURE_CREDENTIALS_ID = 'azure-service-principal'
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                // The cleanup is now handled in the 'post' section.
                checkout scm
                stash includes: '**/*', name: 'source'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    apt update
                    apt install -y curl jq git unzip
                '''
            }
        }

        stage('Download cortexcli') {
            steps {
                script {
                    def response = sh(
                        script: """
                            curl --location '${env.CORTEX_API_URL}/public_api/v1/unified-cli/releases/download-link?os=linux&architecture=amd64' \\
                              --header 'Authorization: ${env.CORTEX_API_KEY}' \\
                              --header 'x-xdr-auth-id: ${env.CORTEX_API_KEY_ID}' \\
                              --silent
                        """, returnStdout: true
                    ).trim()

                    def downloadUrl = sh(
                        script: """echo '${response}' | jq -r '.signed_url'""",
                        returnStdout: true
                    ).trim()

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
                    // Permission fix for stashed files
                    sh 'chmod -R 777 terraform || true'
                    sh 'chown -R $(id -u):$(id -g) terraform || true'

                    // Debug directory
                    sh 'ls -l'
                    sh 'ls -l terraform || true'

                    sh """
                        ./cortexcli \\
                          --api-base-url "${env.CORTEX_API_URL}" \\
                          --api-key "${env.CORTEX_API_KEY}" \\
                          --api-key-id "${env.CORTEX_API_KEY_ID}" \\
                          code scan \\
                          --directory "terraform/" \\
                          --repo-id smuruhesan/cortex-cloud-lab \\
                          --branch "main" \\
                          --source "JENKINS" \\
                          --create-repo-if-missing
                    """
                }
            }
        }

        stage('Deploy Azure Infrastructure') {
            steps {
                script {
                    unstash 'source'
                    // Permission fix for stashed files
                    sh 'chmod -R 777 terraform || true'
                    sh 'chown -R $(id -u):$(id -g) terraform || true'

                    // Debug directory
                    sh 'ls -l'
                    sh 'ls -l terraform || true'
                    sh 'cat terraform/main.tf || true'

                    // Install Terraform if necessary (do NOT delete any folder named 'terraform'!)
                    sh '''
                        if ! command -v terraform >/dev/null; then
                            echo "Terraform not found, installing..."
                            curl -LO https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip
                            unzip -o terraform_1.7.5_linux_amd64.zip
                            mv terraform /usr/local/bin/
                            rm terraform_1.7.5_linux_amd64.zip
                        fi
                        terraform -version
                    '''

                    // This should match your GitHub repo structure (change if needed)
                    def repoId = "smuruhesan/cortex-cloud-lab"
                    def githubUsername = repoId.split('/')[0]

                    // Use Jenkins Azure SP credential, will set env vars for terraform-azure provider
                    withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                        dir('terraform') {
                            sh 'ls -l' // Sanity check again
                            sh 'rm -f .terraform.lock.hcl || true'
                            sh 'terraform init'
                            // If you want to pass vars: change below as needed
                            sh """terraform plan -out=tfplan -var='username=${githubUsername}' || terraform plan -out=tfplan"""
                            // 'username' is just an example, make sure you have a variable block for it
                            sh 'terraform apply -auto-approve tfplan'
                            // The post-build script will handle the .terraform folder cleanup.
                        }
                    }
                }
            }
        }
    }
    
    // NEW: Post-build actions for cleanup
    post {
        always {
            script {
                // Forcefully remove the .terraform directory from within the container
                // This prevents the "Operation not permitted" error on the next build's deleteDir() step
                sh 'rm -rf terraform/.terraform || true'
                sh 'echo "Post-build cleanup completed. The .terraform directory has been removed."'
            }
        }
    }
}
