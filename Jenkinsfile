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
                echo 'Hello from Jenkins - Day 8 pipeline is running!'
                sh 'python3 --version || python --version'
            }
        }
    }

    post {
        always {
            echo 'Day 8 pipeline finished.'
        }
    }
}
