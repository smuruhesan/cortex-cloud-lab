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
                apt install -y curl jq git unzip
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

        stage('Install Terraform') {
            steps {
                sh '''
                curl -o terraform.zip https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip
                unzip terraform.zip
                chmod +x terraform
                mv terraform /usr/local/bin/
                terraform --version
                '''
            }
        }

        stage('Terraform Init and Plan') {
            steps {
                unstash 'source'
                withCredentials([azureServicePrincipal('azure-service-principal')]) {
                    sh '''
                    az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
                    terraform init
                    terraform plan -out=tfplan
                    '''
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                unstash 'source'
                withCredentials([azureServicePrincipal('azure-service-principal')]) {
                    sh 'terraform apply tfplan'
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up Azure resources...'
            withCredentials([azureServicePrincipal('azure-service-principal')]) {
                sh 'terraform destroy -auto-approve'
            }

            echo 'Cleaning up the workspace...'
            cleanWs()

            echo 'Cleanup complete.'
        }
    }
}
