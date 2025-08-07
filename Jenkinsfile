// AZURE AZ command error



pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0'
            args '-u root'
        }
    }

    environment {
        CORTEX_API_KEY = credentials('CORTEX_API_KEY')
        CORTEX_API_KEY_ID = credentials('CORTEX_API_KEY_ID')
        CORTEX_API_URL = 'https://api-tac-x5.xdr.sg.paloaltonetworks.com'
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
        stage('Install Azure CLI and Terraform') {
            steps {
                sh '''
                apt-get update && apt-get install -y curl unzip
                curl -sL https://aka.ms/InstallAzureCliDeb | bash
                curl -o terraform.zip https://releases.hashicorp.com/terraform/1.12.2/terraform_1.12.2_linux_amd64.zip
                rm -rf terraform
                unzip -o terraform.zip
                mv terraform /usr/local/bin/
                az --version
                terraform --version
                '''
            }
        }



stage('Terraform Init and Plan') {
    steps {
        unstash 'source'
        withCredentials([azureServicePrincipal('azure-service-principal')]) {
            dir('terraform') {
                sh """
                pwd
                ls -l

                az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
                
                export ARM_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID}"
                
                # Dynamically set the username from the GIT_URL and export it to Terraform
                export TF_VAR_username=$(echo "${GIT_URL}" | cut -d'/' -f4)
                
                # Dynamically set the resource group name using the username
                RG_NAME="${TF_VAR_username}-vulnerable-terraform-rg"
                
                # Initialize Terraform first
                terraform init
                
                # Attempt to import the existing resource group into Terraform state
                echo "Importing existing resource group into Terraform state..."
                terraform import azurerm_resource_group.vulnerable_rg /subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/${RG_NAME} || true
                
                # Now run the plan to check for changes
                terraform plan -out=tfplan
                """
            }
        }
    }
}
        

        stage('Terraform Apply') {
            steps {
                unstash 'source'
                sh 'ls -l'
                sh 'pwd'
                withCredentials([azureServicePrincipal('azure-service-principal')]) {
                    dir('terraform') {
                        sh '''
                        ls -l
                        pwd
                        
                        az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
                        
                        export ARM_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID}"
                        
                        terraform apply tfplan
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up Azure resources...'
            withCredentials([azureServicePrincipal('azure-service-principal')]) {
                sh '''
                if [ -x "$(command -v terraform)" ]; then
                  echo "Terraform is installed. Proceeding with destroy."
                  terraform destroy -auto-approve
                else
                  echo "Terraform is not found. Installing for cleanup..."
                  curl -o terraform.zip https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
                  rm -rf terraform
                  unzip -o terraform.zip
                  chmod +x terraform
                  mv terraform /usr/local/bin/
                  terraform destroy -auto-approve
                fi
                '''
            }
            echo 'Cleaning up the workspace...'
            cleanWs()
            echo 'Cleanup complete.'
        }
    }
}
