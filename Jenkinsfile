pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage('Hello') {
            steps {
                echo 'Hello from Jenkins - Day 10 pipeline is running!'
                sh 'python3 --version || python --version'
            }
        }

        stage('Build') {
            steps {
                echo 'Building: compiling the app and its tests.'
                sh 'python3 -m py_compile app.py test_app.py'
            }
        }

        stage('Test') {
            steps {
                echo 'Testing: running the app tests.'
                sh 'python3 -m unittest -v'
            }
        }

        stage('Build Image') {
            steps {
                echo 'Building: Docker image my-app:day10.'
                sh 'docker build -t my-app:day10 .'
            }
        }

        stage('Push Image') {
            steps {
                echo 'Pushing: tagging the day10 image and pushing it to Docker Hub.'
                withCredentials([usernamePassword(credentialsId: 'docker-hub', usernameVariable: 'DOCKER_HUB_USER', passwordVariable: 'DOCKER_HUB_PASS')]) {
                    sh '''
                        echo "$DOCKER_HUB_PASS" | docker login -u "$DOCKER_HUB_USER" --password-stdin
                        docker tag my-app:day10 "$DOCKER_HUB_USER/my-app:day10"
                        docker push "$DOCKER_HUB_USER/my-app:day10"
                        docker logout
                    '''
                }
            }
        }
    }

    post {
        always {
            echo 'Day 10 pipeline finished.'
        }
        success {
            echo 'Day 10 pipeline is green: build, tests and Docker Hub push passed.'
        }
        failure {
            echo 'Day 10 pipeline went red: check the Build, Test, Build Image or Push Image stage above.'
        }
    }
}
