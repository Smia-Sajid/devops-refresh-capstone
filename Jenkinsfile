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
                echo 'Hello from Jenkins - Day 9 pipeline is running!'
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
    }

    post {
        always {
            echo 'Day 9 pipeline finished.'
        }
        success {
            echo 'Day 9 pipeline is green: build and tests passed.'
        }
        failure {
            echo 'Day 9 pipeline went red: check the Build or Test stage above.'
        }
    }
}
