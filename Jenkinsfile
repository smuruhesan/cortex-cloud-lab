// FINAL JENKINSFILE

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
                        curl --location '${env.CORTEX_API_URL}/public_api/v1/unified-cli/releases/download-link?os=linux&architecture=amd64' \\
                          --header 'Authorization: ${env.CORTEX_API_KEY}' \\
                          --header 'x-xdr-auth-id: ${env.CORTEX_API_KEY_ID}' \\
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
            steps {
                script {
                    unstash 'source'
                    sh """
                    ./cortexcli \\
                      --api-base-url "${env.CORTEX_API_URL}" \\
                      --api-key "${env.CORTEX_API_KEY}" \\
                      --api-key-id "${env.CORTEX_API_KEY_ID}" \\
                      code scan \\
                      --directory "\$(pwd)" \\
                      --repo-id smuruhesan/cortex-cloud-lab \\
                      --branch "main" \\
                      --source "JENKINS" \\
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
                        
                        USERNAME=$(echo "${GIT_URL}" | cut -d'/' -f4)
                        
                        RG_NAME="${USERNAME}-vulnerable-terraform-rg"
                        
                        terraform init -var="username=${USERNAME}"
                        
                        echo "Importing existing resource group into Terraform state..."
                        terraform import -var="username=${USERNAME}" azurerm_resource_group.vulnerable_rg /subscriptions/${ARM_SUBSCRIPTION_ID}/resourceGroups/${RG_NAME} || true
                        
                        terraform plan -out=tfplan -var="username=${USERNAME}"
                        """
                    }
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                unstash 'source'
                withCredentials([azureServicePrincipal('azure-service-principal')]) {
                    dir('terraform') {
                        sh """
                        az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
                        
                        export ARM_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID}"
                        
                        USERNAME=$(echo "${GIT_URL}" | cut -d'/' -f4)
                        
                        terraform apply -var="username=${USERNAME}" tfplan
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up Azure resources...'
            withCredentials([azureServicePrincipal('azure-service-principal')]) {
                sh """
                USERNAME=$(echo "${GIT_URL}" | cut -d'/' -f4)
                
                if [ -x "$(command -v terraform)" ]; then
                  echo "Terraform is installed. Proceeding with destroy."
                  RG_NAME="${USERNAME}-vulnerable-terraform-rg"
                  terraform destroy -auto-approve -var="username=${USERNAME}"
                else
                  echo "Terraform is not found. Installing for cleanup..."
                  curl -o terraform.zip https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
                  rm -rf terraform
                  unzip -o terraform.zip
                  chmod +x terraform
                  mv terraform /usr/local/bin/
                  terraform destroy -auto-approve -var="username=${USERNAME}"
                fi
                """
            }
            echo 'Cleaning up the workspace...'
            cleanWs()
            echo 'Cleanup complete.'
        }
    }
}
