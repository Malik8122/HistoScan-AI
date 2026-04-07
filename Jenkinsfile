pipeline {
    agent any

    environment {
        ACR_LOGIN_SERVER = 'histoscanregistry67890.azurecr.io'
        IMAGE_NAME       = 'histoscan-ai'
        RESOURCE_GROUP   = 'histoscan-rg'
        CONTAINER_NAME   = 'histoscan-container'
        AZ_PATH          = '"C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd"'
        NOTIFY_EMAIL     = 'sanyask.malik@gmail.com'
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Checking out from GitHub..."
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building image: ${IMAGE_NAME}:${BUILD_NUMBER}"
                bat "docker build --pull=false -t ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${BUILD_NUMBER} ."
                bat "docker tag ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${BUILD_NUMBER} ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest"
            }
        }

        stage('Push to ACR') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'acr-credentials',
                    usernameVariable: 'ACR_USER',
                    passwordVariable: 'ACR_PASS'
                )]) {
                    bat "docker login ${ACR_LOGIN_SERVER} -u %ACR_USER% -p %ACR_PASS%"
                    bat "docker push ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${BUILD_NUMBER}"
                    bat "docker push ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest"
                }
            }
        }

        stage('Deploy to Azure') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'azure-service-principal',
                        usernameVariable: 'AZ_CLIENT_ID',
                        passwordVariable: 'AZ_CLIENT_SECRET'
                    ),
                    string(credentialsId: 'azure-tenant-id', variable: 'AZ_TENANT')
                ]) {
                    bat "%AZ_PATH% login --service-principal -u %AZ_CLIENT_ID% -p %AZ_CLIENT_SECRET% --tenant %AZ_TENANT%"
                    bat "%AZ_PATH% container delete --resource-group %RESOURCE_GROUP% --name %CONTAINER_NAME% --yes"
                    bat "%AZ_PATH% container create --resource-group %RESOURCE_GROUP% --name %CONTAINER_NAME% --image %ACR_LOGIN_SERVER%/%IMAGE_NAME%:latest --cpu 1 --memory 3 --ports 8501 8000 --ip-address Public --dns-name-label histoscanapp67890 --registry-login-server %ACR_LOGIN_SERVER% --registry-username histoscanregistry67890 --registry-password 2BF95tF0qq9xhL4CrsPWH6SLp0sratyGERxcXDd01dWtOSsMZpzWJQQJ99CDACGhslBEqg7NAAACAZCRJBAD --os-type Linux"
                }
            }
        }

        stage('Cleanup') {
            steps {
                bat "docker rmi ${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${BUILD_NUMBER} || exit 0"
            }
        }
    }

    post {
        success {
            echo "SUCCESS — Build #${BUILD_NUMBER} deployed"
            mail(
                to: "${NOTIFY_EMAIL}",
                subject: "SUCCESS: HistoScan AI Build #${BUILD_NUMBER} Deployed",
                body: """
Hello Sanya,

Your HistoScan AI pipeline completed successfully!

Build Details:
--------------
Build Number  : #${BUILD_NUMBER}
Status        : SUCCESS
Branch        : main
Triggered by  : ${currentBuild.getBuildCauses()[0].shortDescription}
Duration      : ${currentBuild.durationString}

What happened:
- Code pulled from GitHub
- Docker image built and pushed to ACR
- Azure container redeployed with latest image

Live App URL:
http://histoscanapp67890.centralindia.azurecontainer.io:8501

Jenkins Dashboard:
http://localhost:8080/job/HistoScan-AI-Pipeline/${BUILD_NUMBER}/

Regards,
Jenkins CI/CD Bot
HistoScan AI Project
                """
            )
        }

        failure {
            echo "FAILED — check logs above"
            mail(
                to: "${NOTIFY_EMAIL}",
                subject: "FAILED: HistoScan AI Build #${BUILD_NUMBER} Failed",
                body: """
Hello Sanya,

Your HistoScan AI pipeline FAILED and needs attention.

Build Details:
--------------
Build Number  : #${BUILD_NUMBER}
Status        : FAILED
Branch        : main
Duration      : ${currentBuild.durationString}

Action Required:
Check the console output to find the error:
http://localhost:8080/job/HistoScan-AI-Pipeline/${BUILD_NUMBER}/console

Common fixes:
- Docker timeout: run Build Now again
- Azure login: check service principal credentials
- ACR push: check ACR password in Jenkins credentials

Regards,
Jenkins CI/CD Bot
HistoScan AI Project
                """
            )
        }

        always {
            echo "Build #${BUILD_NUMBER} finished: ${currentBuild.result}"
        }
    }
}