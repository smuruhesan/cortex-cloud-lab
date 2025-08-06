pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0'
            // Keeping this as per your working Jenkinsfile
            // If global bypass doesn't work, this might need '--security-opt apparmor=unconfined' again
            args '-u root'
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'

        // NEW: Add Azure Service Principal credential ID for deployment
        // IMPORTANT: Replace 'azure-service-principal' with the actual ID of your Azure Service Principal credential in Jenkins
        AZURE_CREDENTIALS_ID = 'azure-service-principal'
    }

    stages {
        stage('Clean Workspace and Checkout Source Code') { // Combined stage for clarity
            steps {
                deleteDir() // NEW: Cleans up workspace before each build
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
                    // Corrected curl command to be on a single logical line
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
                    unstash 'source' // Unstash source code here for scanning

                    // Debugging: What's in the workspace root AFTER unstash for Run Scan?
                    sh 'echo "--- Run Scan Stage: After unstash ---"'
                    sh 'pwd'
                    sh 'ls -l'
                    sh 'ls -l terraform/' // Should show main.tf and terraform.tfvars

                    sh """
                    ./cortexcli \\
                      --api-base-url "${env.CORTEX_API_URL}" \\
                      --api-key "${env.CORTEX_API_KEY}" \\
                      --api-key-id "${env.CORTEX_API_KEY_ID}" \\
                      code scan \\
                      --directory "terraform/" \\ // IMPORTANT: Point to your terraform directory
                      --repo-id "smuruhesan/cortex-cloud-lab" \\ // IMPORTANT: Update with your forked repo ID (e.g., YOUR_GITHUB_USERNAME/cortex-cloud-lab)
                      --branch "main" \\
                      --source "JENKINS" \\
                      --create-repo-if-missing
                    """
                }
            }
        }

        // NEW STAGE: Automate Azure Infrastructure Deployment
        stage('Deploy Azure Infrastructure (Optional)') {
            steps {
                script {
                    unstash 'source' // Ensure source code is available again in this stage's context

                    // Debugging: What's in the workspace root AFTER unstash for Deploy Stage?
                    sh 'echo "--- Deploy Stage: After unstash ---"'
                    sh 'pwd'
                    sh 'ls -l'
                    sh 'ls -l terraform/' // CRITICAL CHECK: Should show main.tf and terraform.tfvars

                    // Extract GitHub username from the repo-id for dynamic naming.
                    // IMPORTANT: Replace 'YOUR_GITHUB_USERNAME/cortex-cloud-lab' with your actual forked repo ID.
                    def repoId = "YOUR_GITHUB_USERNAME/cortex-cloud-lab"
                    def githubUsername = repoId.split('/')[0]

                    // Install Terraform if not already present in the Docker image.
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
                        dir('terraform') { // Navigate to the directory containing your Terraform files
                            // NEW: Remove the lock file before init to ensure a clean state
                            sh 'rm -f .terraform.lock.hcl' // Workaround for lock file issues

                            // Debugging: Confirm files are here before terraform init
                            sh 'echo "--- Deploy Stage: Inside terraform/ dir before init ---"'
                            sh 'pwd'
                            sh 'ls -l .' // List contents of the current directory (which is now terraform/)

                            sh 'terraform init'
                            sh "terraform plan -out=tfplan -var='username=${githubUsername}'"
                            sh "terraform apply -auto-approve tfplan" // -auto-approve bypasses confirmation (use with caution)
                            
                            // CRITICAL ADDITION: Clean up .terraform directory from within the container
                            sh 'rm -rf .terraform' 
                            sh 'echo "--- Deploy Stage: .terraform directory removed by container ---"'
                        }
                    }
                }
            }
        }
        // The automated cleanup stage is removed as per your request.
        // You will need to perform cleanup manually via Azure CLI/Portal.
    }
}
