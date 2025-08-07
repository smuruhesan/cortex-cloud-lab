pipeline {
    agent {
        docker {
            image 'cimg/node:22.17.0'
            // The pipeline log indicates the container runs as root.
            // The `args` line is a good practice for bypassing AppArmor issues, but not the direct fix for the unstash permission problem.
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
                    // Fix permissions on the unstashed files
                    sh 'chmod -R 777 terraform'
                    sh 'chown -R $(id -u):$(id -g) terraform'

                    // Debug directory
                    sh 'ls -l'
                    sh 'ls -l terraform'

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
                    // Use a temporary block to run as the root user for the unstash command
                    withDockerContainer(image: 'cimg/node:22.17.0', args: '-u root') {
                         unstash 'source'
                    }
                    // The rest of the stage can run under the regular container user
                    sh '''
                        chmod -R 777 terraform || true
                        chown -R $(id -u):$(id -g) terraform || true
                        ls -l
                        ls -l terraform || true
                        cat terraform/main.tf || true
                    '''
                    // Install Terraform and deploy...
                    withCredentials([azureServicePrincipal(credentialsId: env.AZURE_CREDENTIALS_ID)]) {
                        dir('terraform') {
                             sh 'ls -l'
                             sh 'rm -f .terraform.lock.hcl || true'
                             sh 'terraform init'
                             sh "terraform plan -out=tfplan -var='username=${githubUsername}' || terraform plan -out=tfplan"
                             sh 'terraform apply -auto-approve tfplan'
                        }
                    }
                }
            }
        }
    }
}
