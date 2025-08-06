pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0'
            args '-u root --security-opt apparmor=unconfined' 
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
        AZURE_CREDENTIALS_ID = 'azure-service-principal'
        
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                // This is the step that stashes your files.
                // It is a crucial prerequisite for the 'unstash' command.
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
                    
                    // --- ADDED DEBUGGING ---
                    sh 'echo "Contents of current directory before scan:"'
                    sh 'ls -l'
                    sh 'echo "Contents of terraform/ directory before scan:"'
                    sh 'ls -l terraform/'
                    // --- END DEBUGGING ---
                    
                    sh """
                    ./cortexcli \
                      --api-base-url "${env.CORTEX_API_URL}" \
                      --api-key "${env.CORTEX_API_KEY}" \
                      --api-key-id "${env.CORTEX_API_KEY_ID}" \
                      code scan \
                      --directory "\$(pwd)" \
                      --repo-id smuruhesan/cortex-cloud-lab \
                      --branch "main" \
                      --source "JENKINS" \
                      --create-repo-if-missing
                    """
                }
            }
        }

        // NEW STAGE: Automate Azure Infrastructure Deployment
        stage('Deploy Azure Infrastructure (Optional)') {
            steps {
                script {
                    unstash 'source'
                    // --- ADDED DEBUGGING ---
                    sh 'echo "Contents of current directory before scan:"'
                    sh 'ls -l'
                    sh 'echo "Contents of terraform/ directory before scan:"'
                    sh 'ls -l terraform/'
                    // --- END DEBUGGING ---
                    
                    // Extract GitHub username from the repo-id for dynamic naming.
                    // IMPORTANT: Replace 'YOUR_GITHUB_USERNAME/cortex-cloud-lab' with your actual forked repo ID.
                    def repoId = "smuruhesan/cortex-cloud-lab"
                    def githubUsername = repoId.split('/')[0]
        
                    // Install Terraform if not already present in the Docker image.
                    // For production, consider using a custom Docker image with Terraform pre-installed.
                    sh '''
                    if ! command -v terraform &> /dev/null
                    then
                        echo "Terraform not found, installing..."
                        apt update && apt install -y unzip

                        # Clean up any existing terraform binary from its global path
                        rm -f /usr/local/bin/terraform
                        rm -rf /usr/local/bin/terraform/ # Just in case it's a directory

                        # Create /usr/local/bin if it doesn't exist (though it usually does)
                        mkdir -p /usr/local/bin/

                        # Corrected curl command: use -o for output file, URL as last argument
                        curl -o /usr/local/bin/terraform_1.7.5_linux_amd64.zip https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip
                        
                        # Unzip directly into /usr/local/bin/
                        unzip -o /usr/local/bin/terraform_1.7.5_linux_amd64.zip -d /usr/local/bin/
                        
                        # Remove the zip file
                        rm /usr/local/bin/terraform_1.7.5_linux_amd64.zip
                        
                        terraform --version
                    fi
                    '''  
                    // Use withCredentials to inject Azure Service Principal environment variables.
                    // The 'azure-service-principal' ID should match the credential ID you set up in Jenkins.
                    withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                        dir('terraform') {
                            sh 'echo "Contents of current directory right before terraform init (inside dir):"'
                            sh 'ls -l .' // List contents of the current directory (which is now terraform/)

                            sh 'terraform init'
                            sh "terraform plan -out=tfplan -var='username=${githubUsername}'"
                            sh "terraform apply -auto-approve tfplan" // -auto-approve bypasses confirmation (use with caution)
                        }
                    }
                }
            }
        }
    }
}
